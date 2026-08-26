from .commandBuilder import CommandBuilder, line_file
from .login import login
from.client import client
from .logout import logout
from .whoami import whoami
from .course import course
from .assignment import assignment
from .groups import groups

import textwrap
DEFAULT_GROUPING = "group"

  
def main():
    builder = CommandBuilder()
    (builder.addCommand(client, help="Handle GitHub client id and secret (set/get/delete)", epilog=_client_epilog())
        .add_argument("id", nargs="?", help="The github client id") \
        .add_argument("secret", nargs="?", metavar="SECRET",help="The github client secret") 
        .add_argument("--delete",action="store_true",help="Delete the client secret from keyring")
        .add_argument("--show-secret",action="store_true",help="show the secret"))
    builder.addCommand(login, help="github login")
    builder.addCommand(logout, help="github logout")
    builder.addCommand(whoami, help="show data about current github user")
    (builder.addCommand(course, help="Handle a course", epilog=_course_epilog())
        .add_argument("--organization", "-o", help="GitHub organization name")
        .add_argument("--year", "-y",  help="Academic year")
        .add_argument("--semester","-s",  help="Academic semester")
        .add_argument("--course","-c", help="Course section number")
        .add_argument("--update","-u",  action="store_true", help="Update an existing course")
        .add_argument("--delete", action="store_true", help="Delete the course")
        .add_argument("--set-current", action="store_true", help="Set this course as the current course")
        .add_argument("--unset", action="store_true", help="Clear the current course")
        .add_argument("--untrack", action="store_true", help="Remove the course from the local configuration")
        .add_argument("roster", nargs="?", type=line_file, help="Path to a file containing GitHub student accounts, one account per line"))
    (builder.addCommand(assignment, help="Handle an assignment", epilog=_assignment_epilog())
        .add_argument("--organization", "-o", help="GitHub organization name")
        .add_argument("--year", "-y", help="Academic year")
        .add_argument("--semester", "-s", help="Academic semester")
        .add_argument("--course", "-c", help="Course section number")
        .add_argument("--template", "-t", help="GitHub template repository URL")
        .add_argument("--name", "-n", help="Assignment name")
        .add_argument("--private", action="store_true", help="Create private repositories")
        .add_argument("--user", "-u", nargs="+", help="GitHub usernames to process instead of the course students. Useful for teachers")
        .add_argument("--group", nargs="?", const=DEFAULT_GROUPING, help="Create group repositories, optionally specifying the grouping"))
    (builder.addCommand(groups,help="Handle the groups of a course",epilog=_groups_epilog())
        .add_argument("--organization", "-o", help="GitHub organization name")
        .add_argument("--year", "-y", help="Academic year")
        .add_argument("--semester", "-s", help="Academic semester")
        .add_argument("--course", "-c", help="Course section number")
        .add_argument("--grouping", "-g", default=DEFAULT_GROUPING, help="Group grouping name. Useful for using different sets of students for different assignments")
        .add_argument("--delete", action="store_true", help="Delete all groups in the grouping")
        .add_argument("--list-groupings", "-l", action="store_true", help="List groupings of the course")
        .add_argument("roster",nargs="?",type=line_file,help="Path to a file containing GitHub usernames, one group per line with users separated by spaces",
        ))    
    builder.run()

def _client_epilog():
    return textwrap.dedent("""
        Examples:
            Save client secret:
                classroom client my-id my-secret-value

            Show current client id:
                classroom client

            Show current client id and secret:
                classroom client --show-secret

            Delete client id and secret:
                classroom client --delete
    """)

def _course_epilog():
    return textwrap.dedent("""
        A current course can be configured to avoid specifying the course
        in every command. This is convenient if you usually work with a
        single course. If you prefer to be explicit, you can specify the
        course in each command instead.

        To help prevent accidental changes, course modification commands
        always require the course to be specified explicitly. The current
        course is only used by commands that operate on a course, not by
        commands that modify its definition.

        Examples:

            Create a course:
                classroom course -o obj1unq -y 2026 -s 1 -c 1 roster.txt

            Update an existing course:
                classroom course -o obj1unq -y 2026 -s 1 -c 1 --update roster.txt

            Delete a course:
                classroom course -o obj1unq -y 2026 -s 1 -c 1 --delete

            Show information about a course:
                classroom course -o obj1unq -y 2026 -s 1 -c 1

            Set the current course:
                classroom course -o obj1unq -y 2026 -s 1 -c 1 --set

            Unset the current course:
                classroom course --unset

            Show the current course and the list of tracked courses:
                classroom course

            Untrack a course:
                classroom course -o obj1unq -y 2026 -s 1 -c 1 --untrack
        """)

def _groups_epilog():
    return textwrap.dedent("""
    Groups are organized into groupings. A grouping represents a particular
    way of dividing the students of a course into groups. The default grouping
    is "group".

    Each line in the roster represents one group, with GitHub usernames
    separated by spaces. Groups are numbered according to their order in the
    roster, starting at 1.

    Group teams are created using the following naming convention:

        <course>_<grouping>_<number>

    Examples:

        Create the default grouping for the current course:
            classroom groups groups.txt

        Create a grouping called "tp1":
            classroom groups -g tp1 tp1-groups.txt

        Show the groups in the default grouping:
            classroom groups

        Show the groups in a specific course:
            classroom groups -o obj1unq -y 2026 -s 2 -c 2

        Show the "tp1" grouping:
            classroom groups -g tp1

        Delete all groups in the default grouping:
            classroom groups --delete

        Delete all groups in the "tp1" grouping:
            classroom groups -g tp1 --delete

    When a roster is provided, the command creates or updates the grouping
    to match the roster. Running the same command multiple times is safe.

    The --delete option removes all groups belonging to the selected grouping.
    It cannot be used together with a roster.

    If neither a roster nor --delete is provided, the command only displays
    the groups in the selected grouping.

    The --grouping option is useful when the same course needs different
    group configurations for different assignments. For example, "group"
    can contain the groups used throughout the course, while "tp1" and "tp2"
    can contain different groupings for specific assignments.
    """)

def _assignment_epilog():
    return textwrap.dedent("""
        Assignments are created individually by default. Use --group to create
        an assignment for the groups of a course.

        A current course is used when no course is specified.

        Examples:

            Create an individual assignment in the current course:
                classroom assignment -t https://github.com/obj1unq/pepitaEnunciado

            Create an individual assignment specifying the course:
                classroom assignment -o obj1unq -y 2026 -s 2 -c 2 -t https://github.com/obj1unq/pepitaEnunciado

            Create an individual assignment with a custom name:
                classroom assignment -t https://github.com/obj1unq/pepitaEnunciado -n tp1

            Create private repositories:
                classroom assignment -t https://github.com/obj1unq/pepitaEnunciado --private

            Create an individual assignment for specific users instead of the course students:
                classroom assignment -t https://github.com/obj1unq/pepitaEnunciado -u lgassman otro_usuario

            Create a group assignment using the default grouping:
                classroom assignment -t https://github.com/obj1unq/pepitaEnunciado --group

            Create a group assignment using a specific grouping:
                classroom assignment -t https://github.com/obj1unq/pepitaEnunciado --group tp1groups

            List assignments in the current course:
                classroom assignment

            List assignments in a specific course:
                classroom assignment -o obj1unq -y 2026 -s 2 -c 2

            List repositories for an assignment:
                classroom assignment -n tp1

        The --user option processes the specified GitHub users instead of the
        students in the course. This can be useful for teachers who need to
        create or clone their own assignment repositories.

        The --group option creates repositories for the groups in the course.
        When no grouping is specified, the default grouping is "groups".

        Without --template, the command only queries existing assignments
        and repositories. The --name option selects a specific assignment.

        """)



if __name__ == "__main__":
    raise SystemExit(main())