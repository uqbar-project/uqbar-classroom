import logging
from abc import ABC, abstractmethod
from typing import Iterator

from requests import HTTPError

from .course import show_pending_students, specified_course_or_current
from .models import RepoTemplate
from .requests import request
from .teams import find_team_members
from .groups import find_groupings, find_groups, find_group_members


FEEDBACK_COMMIT_MESSAGE = "Initial feedback commit"
INITIAL_COMMITS = 2


class RepoCreator(ABC):
    def __init__(self, course, template, assignment_name):
        self.course = course
        self.template = template
        self.assignment_name = assignment_name

    @property
    def orga(self):
        return self.course.organization

    def repository_name(self):
        return f"{self.course.name}_{self.assignment_name}_{self.repository_suffix()}"

    @abstractmethod
    def agent(self):
        pass

    def add_access(self):
        response = request("PUT", self.access_endpoint(), json={"permission": "push"})
        if response.status_code == 422:
            logging.info(f"'{self.agent()}' probably already has access to repository '{self.repository_name()}'")
        else:
            logging.info(f"Added '{self.agent()}' to repository '{self.repository_name()}': {response.status_code}")

    @abstractmethod
    def repository_suffix(self):
        pass

    @abstractmethod
    def access_endpoint(self):
        pass

    def create(self):
        self._create_repository()
        self.add_access()
        self._create_feedback_branch()
        commit_sha = self._create_feedback_commit()
        self._update_default_branch(commit_sha)
        self._create_feedback_pull_request()


    def _create_repository(self):
        name = self.repository_name()
        response = request("POST", f"https://api.github.com/repos/{self.template.owner}/{self.template.name}/generate",
            json={"owner": self.orga, "name": name, "private": self.template.private, "include_all_branches": self.template.include_all_branches})

        if response.status_code == 422:
            logging.info(f"Repository '{name}' probably already exists")
        else:
            logging.warning(f"Created repository {name} OK: {response.status_code}")

    def _create_feedback_branch(self):
        name = self.repository_name()
        response = request("GET", f"https://api.github.com/repos/{self.orga}/{name}/commits/{self.template.default_branch}")
        sha = response.json()["sha"]

        response = request("POST", f"https://api.github.com/repos/{self.orga}/{name}/git/refs",
            json={"ref": "refs/heads/feedback", "sha": sha})

        if response.status_code == 422:
            logging.info(f"Branch 'feedback' in repository '{name}' probably already exists")
        else:
            logging.info(f"Created branch 'feedback' in repository '{name}': {response.status_code}")

    def _create_feedback_commit(self):
        name = self.repository_name()
        repo_url = f"https://api.github.com/repos/{self.orga}/{name}"
        commits = request("GET", f"{repo_url}/commits?sha={self.template.default_branch}&per_page=100").json()

        commit = next((commit for commit in commits if commit["commit"]["message"].splitlines()[0] == FEEDBACK_COMMIT_MESSAGE),None)

        if commit:
            logging.info(f"Feedback baseline already exists in repository '{name}'")
            return commit["sha"]

        main_sha = request("GET", f"{repo_url}/git/ref/heads/{self.template.default_branch}").json()["object"]["sha"]
        tree_sha = request("GET", f"{repo_url}/git/commits/{main_sha}").json()["tree"]["sha"]

        response = request("POST", f"{repo_url}/git/commits",json={"message": FEEDBACK_COMMIT_MESSAGE, "tree": tree_sha, "parents": [main_sha]})

        response.raise_for_status()

        commit_sha = response.json()["sha"]
        logging.info(f"Created feedback baseline commit in repository '{name}'")
        return commit_sha

    def _update_default_branch(self, commit_sha):
        name = self.repository_name()
        repo_url = f"https://api.github.com/repos/{self.orga}/{name}"
        response = request("PATCH", f"{repo_url}/git/refs/heads/{self.template.default_branch}", json={"sha": commit_sha})

        response.raise_for_status()
        logging.info(f"Updated default branch '{self.template.default_branch}' in repository '{name}'")

    def _create_feedback_pull_request(self):
        name = self.repository_name()
        response = request("POST", f"https://api.github.com/repos/{self.orga}/{name}/pulls",
            json={"title": "feedback", "head": self.template.default_branch, "base": "feedback"})

        if response.status_code == 422:
            logging.info(f"Feedback pull request in repository '{name}' probably already exists")
        else:
            logging.info(f"Created feedback pull request in repository '{name}': {response.status_code}")


class IndividualRepoCreator(RepoCreator):
    def __init__(self, course, template, assignment_name, user):
        super().__init__(course, template, assignment_name)
        self.user = user

    def repository_suffix(self):
        return self.user['login'].lower()

    def agent(self):
        return self.user['login']

    def access_endpoint(self):
        return f"https://api.github.com/repos/{self.orga}/{self.repository_name()}/collaborators/{self.user['login']}"
    


class GroupRepoCreator(RepoCreator):
    def __init__(self, course, template, assignment_name, group):
        super().__init__(course, template, assignment_name)
        self.group = group

    def agent(self):
        return self.group["slug"]

    def repository_suffix(self):
        return self.group["slug"].removeprefix(f"{self.course.name}-")

    def access_endpoint(self):
        return f"https://api.github.com/orgs/{self.orga}/teams/{self.group['slug']}/repos/{self.orga}/{self.repository_name()}"



def assignment(organization, year, semester, course, template, name, private, user, group):
    specified_course = specified_course_or_current(organization, year, semester, course)

    if user and not template:
        raise ValueError("--user can only be used when creating an assignment")

    if group and not template:
        raise ValueError("--group can only be used when creating an assignment")

    if group and user:
        raise ValueError("--group and --user are mutually exclusive")

    if template:
        return _create_assignment(specified_course, template, name, private, user, group)

    if name:
        return _show_assignment(specified_course, name)

    return _show_assignments(specified_course)


def _create_assignment(course, template, name, private, users, grouping):
    template = RepoTemplate.from_str(template, private=private)
    _find_default_branch(template)

    if not name:
        name = template.name

    errors = []
    success = 0

    for creator in _get_assignment_creators(course, users, grouping, template, name):
        try:
            logging.info(f"Working with {creator.repository_name()}")
            creator.create()
            success += 1
        except KeyError as e:
            if e.args[0] == "login":
                error = f"No login name for {creator}"
                logging.debug(error)
                errors.append(error)
            else:
                raise
        except HTTPError as e:
            error = f"{creator.repository_name()}: Error {e.response.status_code} creating assignment: {e.response.text}"
            logging.debug(error)
            errors.append(error)
        finally:
            logging.info("---")

    logging.info(f"Successfully processed: {success}, errors: {len(errors)}")

    for error in errors:
        logging.error(error)

def _get_assignment_creators(course, users, grouping, template, name) -> Iterator[RepoCreator]:
    if grouping:
        found = False

        for _, group in find_groups(course, grouping):
            found = True
            yield GroupRepoCreator(course, template, name, group)

        if not found:
            raise ValueError(f"Grouping '{grouping}' does not exist in course '{course.name}'")

        return

    users = ({"login": username} for username in users) if users else find_team_members(course.organization, course.name)

    found = False

    for user in users:
        found = True
        yield IndividualRepoCreator(course, template, name, user)

    if not found:
        raise ValueError(f"No users found for assignment in course '{course.name}'")


def _find_default_branch(template):
    response = request("GET", f"https://api.github.com/repos/{template.owner}/{template.name}")
    template.default_branch = response.json()["default_branch"]


class AssignmentReporter(ABC):
    def __init__(self, owners): 
        """owners maps each owner to a tuple containing repository data."""
        self.owners = owners
    
    @abstractmethod
    def owners_description(self):
        pass

    def process_repo_data(self, owner, data):
        logging.info(self.repo_data_str(owner, data))

    def repo_data_str(self, owner, data):
        return f"- {owner}, {data[1]}: commits, repo:{data[0]['html_url']}"         
        
    def show(self):
        logging.info("---")
        logging.info(f"{self.owners_description()} repositories ({len(self.owners)})")
        for owner, data in self.owners.items():
            self.process_repo_data(owner, data)

class FollowingAssignmentReporter(AssignmentReporter):
    #Hace énfasis en quienes no hicieron commits
    def __init__(self, owners, expected_owners): 
        super().__init__(owners)
        self.without_commits = []
        self._expected_owners = expected_owners

    def process_repo_data(self, owner, data):
        super().process_repo_data(owner, data)
        if data[1] == 0:
            self.without_commits.append(owner)

    def show(self):
        super().show()
        if self.without_commits:
            logging.info(f"{self.owners_description()} without commits:")
            for owner in self.without_commits:
                logging.info(f"-{self.name(owner)}")

        missing_owner = self.expected_owners() - self.owners.keys()
        if missing_owner:
            logging.info(f"Missing {self.owners_description().lower()}")
            for owner in missing_owner:
                logging.info(f"-{self.name(owner)}")

    def name(self, owner):
        return owner

    def expected_owners(self):
        return self._expected_owners

class StudentAssignmentReporter(FollowingAssignmentReporter):
    def __init__(self, owners, expected_owners, course):
        super().__init__(owners, expected_owners)
        self.course = course

    def owners_description(self):
        return "Students"

    def show(self):
        super().show()
        show_pending_students(self.course)


class NonStudentAssignmentReporter(AssignmentReporter):
    def owners_description(self):
        return "Non-students"

class GroupAssignmentReporter(FollowingAssignmentReporter):

    def __init__(self, owners, expected_groups, grouping): 
        #owners es un dict de owner a una tupla con datos del repositorio
        #mientras que groups es un diccionario de grupo a miembros
        #que oficia de expected_owner de la superclase
        super().__init__(owners, expected_groups)
        self.grouping = grouping

    def owners_description(self):
        return f"Grouping {self.grouping}"

    def repo_data_str(self, owner, data):
        return super().repo_data_str(owner, data) + " members: " + self.members(owner)     

    def members(self,owner):
        return ",".join(self._expected_owners.get(owner, []))
    
    def name(self,owner):
        return f"{owner} ({self.members(owner)})" 

    def expected_owners(self):
        return self._expected_owners.keys()



def _show_assignment(course, name):
    prefix = f"{course.name}_{name}_"
    repositories = _find_assignment_repositories(course.organization, prefix)
    students = {student["login"].lower() for student in find_team_members(course.organization, course.name)}
    groupings = set(find_groupings(course))

    student_repositories = {}
    non_student_repositories = {}
    group_repositories = {}

    logging.debug(f"show assignment for prefix: {prefix}")
    for repository in repositories:
        logging.debug(f"found {repository['name']}")
        suffix = repository["name"][len(prefix):]
        commits = _count_repository_commits(course.organization, repository) - INITIAL_COMMITS

        grouping, group = next(((grouping, suffix[len(grouping) + 1:]) for grouping in groupings if suffix.startswith(f"{grouping}-")), (None, None))
        logging.debug(f"grouping: {grouping}, group:{group}")

        if grouping:
            group_repositories.setdefault(grouping, {})[group] = (repository, commits)
        elif suffix in students:
            logging.debug(f"it is a student repo!")
            student_repositories[suffix]=(repository, commits)
        else:
            logging.debug(f"it is not a student repo!")
            non_student_repositories[suffix]= (repository, commits)

    reporters = []

    if student_repositories:
        reporters.append(StudentAssignmentReporter(student_repositories, students, course))

    if non_student_repositories:
        reporters.append(NonStudentAssignmentReporter(non_student_repositories))

    for grouping, repositories in group_repositories.items():
        expected_groups = {}
        for group_name, _ in find_groups(course, grouping):
            group = group_name.removeprefix(f"{course.name}-{grouping}-")
            expected_groups[group] = [member['login'] for member in find_group_members(course, group_name)]

        reporters.append(GroupAssignmentReporter(repositories, expected_groups, grouping))

    logging.info(f"Assignment '{name}'")

    for reporter in reporters:
        reporter.show()

    if not reporters:
        logging.info("No information available for this assignment")

def _find_assignment_repositories(orga, prefix):
    response = request("GET", "https://api.github.com/search/repositories", params={"q": f"org:{orga} {prefix} in:name", "per_page": 100})

    return [repository for repository in response.json()["items"] if repository["name"].startswith(prefix)]


def _count_repository_commits(orga, repository):
    response = request("GET", f"https://api.github.com/repos/{orga}/{repository['name']}/commits", params={"sha": repository["default_branch"], "per_page": 100})
    return len(response.json())


def _show_assignments(course):
    prefix = f"{course.name}_"
    repositories = _find_assignment_repositories(course.organization, prefix)

    assignments = {}

    for repository in repositories:
        assignment = repository["name"][len(prefix):].rsplit("_", 1)[0]
        assignments[assignment] = assignments.get(assignment, 0) + 1

    for assignment in sorted(assignments):
        logging.info(f"{assignment} ({assignments[assignment]} repositories)")