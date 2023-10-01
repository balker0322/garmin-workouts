from garminworkouts.workoutexporter import WorkoutExporter
import datetime


def main():
    running_program_file = r'sample_yaml.yaml'
    running_pace_file = r'running_workouts\pace\pace.yaml'
    race_date = datetime.datetime(2023,11,19)

    username = ''
    password = ''

    w = WorkoutExporter(username, password)
    w.import_running_program(
        running_program_file,
        running_pace_file,
        race_date)



if __name__=='__main__':
    main()



