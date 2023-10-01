#!/usr/bin/env python3

import argparse
import glob
import logging
import os

from garminworkouts.config import configreader
from garminworkouts.garmin.garminclient import GarminClient
from garminworkouts.models.workout import Workout, RunningWorkout
from garminworkouts.utils.validators import writeable_dir
from getpass import getpass
import datetime

# import account


def command_import_run(args):
    workout_files = glob.glob(r'running_workouts/*.yaml')

    workout_configs = [configreader.read_config(workout_file) for workout_file in workout_files]
    target_pace = configreader.read_config(os.path.join(r'running_workouts/pace', args.pace))
    workouts = [RunningWorkout(workout_config, target_pace) for workout_config in workout_configs]

    with _garmin_client(args) as connection:
        existing_workouts_by_name = {Workout.extract_workout_name(w): w for w in connection.list_workouts()}

        for workout in workouts:
            workout_name = workout.get_workout_name()
            existing_workout = existing_workouts_by_name.get(workout_name)

            if existing_workout:
                workout_id = Workout.extract_workout_id(existing_workout)
                workout_owner_id = Workout.extract_workout_owner_id(existing_workout)
                payload = workout.create_workout(workout_id, workout_owner_id)
                logging.info("Updating workout '%s'", workout_name)
                connection.update_workout(workout_id, payload)
            else:
                payload = workout.create_workout()
                logging.info("Creating workout '%s'", workout_name)
                connection.save_workout(payload)


def import_run_workout(connection, workout_files_dir, pace_file, start_date=None):
    workout_files = glob.glob(workout_files_dir)

    workout_configs = [configreader.read_config(workout_file) for workout_file in workout_files]
    target_pace = configreader.read_config(pace_file)
    workouts = [RunningWorkout(workout_config, target_pace) for workout_config in workout_configs]

    existing_workouts_by_name = {Workout.extract_workout_name(w): w for w in connection.list_workouts()}

    for workout in workouts:
        workout_name = workout.get_workout_name()
        existing_workout = existing_workouts_by_name.get(workout_name)

        if existing_workout:
            workout_id = Workout.extract_workout_id(existing_workout)
            workout_owner_id = Workout.extract_workout_owner_id(existing_workout)
            payload = workout.create_workout(workout_id, workout_owner_id)
            logging.info("Updating workout '%s'", workout_name)
            connection.update_workout(workout_id, payload)
        else:
            payload = workout.create_workout()
            logging.info("Creating workout '%s'", workout_name)
            connection.save_workout(payload)
    
    if start_date is not None:
        schedule_run_workout(connection, workout_files_dir, pace_file, start_date)


def schedule_run_workout(connection, workout_files_dir, pace_file, start_date):
    workout_files = glob.glob(workout_files_dir)

    workout_configs = [configreader.read_config(workout_file) for workout_file in workout_files]
    target_pace = configreader.read_config(pace_file)
    workouts = [RunningWorkout(workout_config, target_pace) for workout_config in workout_configs]

    existing_workouts_by_name = {Workout.extract_workout_name(w): w for w in connection.list_workouts()}

    for workout in workouts:
        workout_name = workout.get_workout_name()
        existing_workout = existing_workouts_by_name.get(workout_name)

        day_delta = {
            'recovery run a':0,
            'recovery run b':1,
            'speed run':2,
            'recovery run c':3,
            'long run':4,
        }

        def get_date():
            run_workout_time = ' '.join(workout_name.split()[1:])
            date = start_date + datetime.timedelta(days=day_delta[run_workout_time])
            return date.strftime("%Y-%m-%d")

        existing_workout = existing_workouts_by_name.get(workout_name)
        workout_id = Workout.extract_workout_id(existing_workout)
        connection.schedule_workout(workout_id, get_date())


def command_import(args):
    workout_files = glob.glob(args.workout)

    workout_configs = [configreader.read_config(workout_file) for workout_file in workout_files]
    workouts = [Workout(workout_config, args.ftp, args.target_power_diff) for workout_config in workout_configs]

    with _garmin_client(args) as connection:
        existing_workouts_by_name = {Workout.extract_workout_name(w): w for w in connection.list_workouts()}

        for workout in workouts:
            workout_name = workout.get_workout_name()
            existing_workout = existing_workouts_by_name.get(workout_name)

            if existing_workout:
                workout_id = Workout.extract_workout_id(existing_workout)
                workout_owner_id = Workout.extract_workout_owner_id(existing_workout)
                payload = workout.create_workout(workout_id, workout_owner_id)
                logging.info("Updating workout '%s'", workout_name)
                connection.update_workout(workout_id, payload)
            else:
                payload = workout.create_workout()
                logging.info("Creating workout '%s'", workout_name)
                connection.save_workout(payload)


def command_export(args):
    with _garmin_client(args) as connection:
        for workout in connection.list_workouts():
            workout_id = Workout.extract_workout_id(workout)
            workout_name = Workout.extract_workout_name(workout)
            file = os.path.join(args.directory, str(workout_id)) + ".fit"
            logging.info("Exporting workout '%s' into '%s'", workout_name, file)
            connection.download_workout(workout_id, file)


def command_list(args):
    with _garmin_client(args) as connection:
        for workout in connection.list_workouts():
            Workout.print_workout_summary(workout)


def command_schedule(args):
    with _garmin_client(args) as connection:
        workout_id = args.workout_id
        date = args.date
        connection.schedule_workout(workout_id, date)


def command_get(args):
    with _garmin_client(args) as connection:
        workout = connection.get_workout(args.id)
        Workout.print_workout_json(workout)


def command_delete(args):
    with _garmin_client(args) as connection:
        logging.info("Deleting workout '%s'", args.id)
        connection.delete_workout(args.id)


def _garmin_client(args, account=None):
    
    if account:
        username = account['username']
        password = account['password']
    else:
        username = input('Enter username: ')
        password = getpass('Enter password: ')

    client =  GarminClient(
        connect_url=args.connect_url,
        sso_url=args.sso_url,
        # username=account.USERNAME,
        # password=account.PASSWORD,
        username = username,
        password = password,
        # cookie_jar=args.cookie_jar
        cookie_jar=None
    )
    print(args.connect_url)
    print(args.sso_url)
    print(f'Done authenticating: {username}')
    return client


def main():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="Manage Garmin Connect workout(s)")
    # parser.add_argument("--username", "-u", required=True, help="Garmin Connect account username")
    # parser.add_argument("--password", "-p", required=True, help="Garmin Connect account password")
    parser.add_argument("--cookie-jar", default=".garmin-cookies.txt", help="Filename with authentication cookies")
    parser.add_argument("--connect-url", default="https://connect.garmin.com", help="Garmin Connect url")
    parser.add_argument("--sso-url", default="https://sso.garmin.com", help="Garmin SSO url")
    parser.add_argument("--debug", action='store_true', help="Enables more detailed messages")

    subparsers = parser.add_subparsers(title="Commands")

    parser_import = subparsers.add_parser("import", description="Import workout(s) from file(s) into Garmin Connect")
    parser_import.add_argument("workout",
                               help="File(s) with workout(s) to import, "
                                    "wildcards are supported e.g: sample_workouts/*.yaml")
    parser_import.add_argument("--ftp", required=True, type=int,
                               help="FTP to calculate absolute target power from relative value")
    parser_import.add_argument("--target-power-diff", default=0.05, type=float,
                               help="Percent of target power to calculate final target power range")
    parser_import.set_defaults(func=command_import)

    parser_export = subparsers.add_parser("export",
                                          description="Export all workouts from Garmin Connect and save into directory")
    parser_export.add_argument("directory", type=writeable_dir,
                               help="Destination directory where workout(s) will be exported")
    parser_export.set_defaults(func=command_export)

    parser_list = subparsers.add_parser("list", description="List all workouts")
    parser_list.set_defaults(func=command_list)

    parser_schedule = subparsers.add_parser("schedule", description="Schedule a workouts")
    parser_schedule.add_argument("--workout_id", "-w", required=True, help="Workout id to schedule")
    parser_schedule.add_argument("--date", "-d", required=True, help="Date to which schedule the workout")
    parser_schedule.set_defaults(func=command_schedule)

    parser_get = subparsers.add_parser("get", description="Get workout")
    parser_get.add_argument("--id", required=True, help="Workout id, use list command to get workouts identifiers")
    parser_get.set_defaults(func=command_get)

    parser_delete = subparsers.add_parser("delete", description="Delete workout")
    parser_delete.add_argument("--id", required=True, help="Workout id, use list command to get workouts identifiers")
    parser_delete.set_defaults(func=command_delete)

    parser_import = subparsers.add_parser("import_run", description="Import workout(s) from file(s) into Garmin Connect")
    parser_import.add_argument("pace",
                               help="File(s) with workout(s) to import, "
                                    "wildcards are supported e.g: sample_workouts/*.yaml")
    parser_import.set_defaults(func=command_import_run)

    args = parser.parse_args()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level)

    args.func(args)

def import_running_workout(args, account, pace_file, wtg, start_date):
    workout_files = os.path.join('nike_42k', f'{wtg:02}', '*.yaml')

    with _garmin_client(args, account) as connection:
        import_run_workout(connection=connection, workout_files_dir=workout_files, pace_file=pace_file, start_date=start_date)



def main2():
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description="Manage Garmin Connect workout(s)")
    # parser.add_argument("--username", "-u", required=True, help="Garmin Connect account username")
    # parser.add_argument("--password", "-p", required=True, help="Garmin Connect account password")
    parser.add_argument("--cookie-jar", default=".garmin-cookies.txt", help="Filename with authentication cookies")
    parser.add_argument("--connect-url", default="https://connect.garmin.com", help="Garmin Connect url")
    parser.add_argument("--sso-url", default="https://sso.garmin.com", help="Garmin SSO url")
    parser.add_argument("--debug", action='store_true', help="Enables more detailed messages")
    args = parser.parse_args()

    logging_level = logging.DEBUG if args.debug else logging.INFO
    logging.basicConfig(level=logging_level)

    date_at_15_wtg = datetime.datetime(2023,5,28)
    wtg = 9
    account = {
        'username':'xxxxxx@xxxx.com',
        'password':'xxxxxx',
    }

    with _garmin_client(args, account) as connection:
        # print(connection.list_workouts())
        pass

    # with _garmin_client(args, account) as connection:
    #     print(connection.list_workouts())


    # for wtg in [8, 7, 6, 5, 4, 3, 2, 1]:
    #     start_date = date_at_15_wtg + datetime.timedelta(days=7*(15-wtg))

    #     account1 = {
    #     }
    #     pace_file1=r'running_workouts/pace/pace2.yaml'

    #     account2 = {
    #     }
    #     pace_file2=r'running_workouts/pace/pace.yaml'

    #     import_running_workout(args, account1, pace_file1, wtg, start_date)
    #     import_running_workout(args, account2, pace_file2, wtg, start_date)

    # race_date = datetime.datetime(2023,9,17)
    # wtg = 1
    # # start_date = date_at_15_wtg + datetime.timedelta(days=7*(15-wtg))
    # start_date = race_date + datetime.timedelta(days=7*(-wtg))
    # print(start_date)
    # account2 = {
    #     'username':'xxxxxx@xxxx.com',
    #     'password':'xxxxxx',
    # }
    # pace_file2=r'running_workouts/pace/pace.yaml'
    # import_running_workout(args, account2, pace_file2, wtg, start_date)

    


if __name__ == "__main__":
    main2()
