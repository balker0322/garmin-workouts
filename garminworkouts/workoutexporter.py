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



class WorkoutExporter:

    __CONNECT_URL = "https://connect.garmin.com"
    __SSO_URL = "https://sso.garmin.com

    def __init__(self, username, password):
        self.__client = __get_garmin_client(username, password)
        
    def __get_garmin_client(self, username, password)->GarminClient:

        client =  GarminClient(
            connect_url=self.__CONNECT_URL,
            sso_url=self.__SSO_URL,
            username = username,
            password = password,
            cookie_jar=None
        )

        return client

    def __parse_multi_running_workout_yaml(self, multi_running_workout_yaml)->list:
        pass

    def import_running_workout(self, workout_file, pace_file=None, start_date=None):
        workout_configs = self.__parse_multi_running_workout_yaml(workout_file)

    def command_import_run(self):
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


    def command_import(self):
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


    def command_export(self):
        with _garmin_client(args) as connection:
            for workout in connection.list_workouts():
                workout_id = Workout.extract_workout_id(workout)
                workout_name = Workout.extract_workout_name(workout)
                file = os.path.join(args.directory, str(workout_id)) + ".fit"
                logging.info("Exporting workout '%s' into '%s'", workout_name, file)
                connection.download_workout(workout_id, file)


    def command_list(self):
        with _garmin_client(args) as connection:
            for workout in connection.list_workouts():
                Workout.print_workout_summary(workout)


    def command_schedule(self):
        with _garmin_client(args) as connection:
            workout_id = args.workout_id
            date = args.date
            connection.schedule_workout(workout_id, date)


    def command_get(self):
        with _garmin_client(args) as connection:
            workout = connection.get_workout(args.id)
            Workout.print_workout_json(workout)


    def command_delete(self):
        with _garmin_client(args) as connection:
            logging.info("Deleting workout '%s'", args.id)
            connection.delete_workout(args.id)
