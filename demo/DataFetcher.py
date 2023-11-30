import pandas as pd
from google.cloud import bigquery
import os
# import sys

class DataFetcher:

    def __init__(self):
        # # add paths to system
        # PATH = '/Users/marialentini/Library/CloudStorage/OneDrive-PearsonPLC/Projects/turbo-job-recommender/'
        # sys.path.insert(0, os.path.abspath(PATH))

        # load train data
        self.X_train = pd.read_csv('data/train_data.csv')

        # connect to bq client via service account credentials
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "google_credentials/pearson-dev-11a710907c16.json"
        self.client = bigquery.Client()

    def fetch_engaged_jobs(self, user_id):
        """
        Engage means click, bookmark or apply, we do not differentiate
        now but we will probabily change this in the future
        """

        clicked_job_ids = self.X_train.loc[self.X_train.person_id == user_id, 'job_id'].unique()
        clicked_job_ids = '(' + ', '.join(['\"'+ x + '\"' for x in clicked_job_ids]) + ')'

        query = """
        SELECT 
            jd.uniq_id as job_id,
            job_type,
            job_description,
            --coalesce(inferred_job_title, job_title) as job_title,
            job_title,
            company_name,
            inferred_job_title,
            inferred_department_name,
            inferred_seniority_level,
            skill_title
        FROM edwa-global.TURBO.S3_TURBO_JOBSPIKR_DETAILS jd
        JOIN edwa-global.TURBO.S3_TURBO_JOBSPIKR_SKILL_DIM sd
            ON jd.uniq_id = sd.uniq_id
        WHERE jd.uniq_id in {}
        """.format(clicked_job_ids)

        clicked_jobs = self.client.query(query).to_dataframe()  # Make an API request.
        clicked_jobs.columns = [x.lower() for x in clicked_jobs.columns]

        return clicked_jobs

    def fetch_recommended_jobs(self, job_ids):
        job_ids = '(' + ', '.join(['\"'+ x + '\"' for x in job_ids]) + ')'

        # get recs meta data from BQ
        query = """
        SELECT 
            jd.uniq_id as job_id,
            job_type,
            job_description,
            coalesce(inferred_job_title, job_title) as job_title,
            company_name,
            inferred_job_title,
            inferred_department_name,
            inferred_seniority_level,
            skill_title
        FROM edwa-global.TURBO.S3_TURBO_JOBSPIKR_DETAILS jd
        JOIN edwa-global.TURBO.S3_TURBO_JOBSPIKR_SKILL_DIM sd
            ON jd.uniq_id = sd.uniq_id
        WHERE jd.uniq_id in {}
        """.format(job_ids)

        job_rec = self.client.query(query).to_dataframe()  # Make an API request.
        job_rec.columns = [x.lower() for x in job_rec.columns]

        return job_rec

    def fetch_user_profile(self, user_id):

        query = """
        SELECT 
            up.person_id,
            js.skill_title,
            jr.role_title,
            DATE_DIFF(
                DATE(SPLIT(eo.graduation_date, "/")[1] || "-" || SPLIT(eo.graduation_date, "/")[0] || "-" || "01"),
                CURRENT_DATE(),
                YEAR
            ) as years_until_grad,
            eo.school_id,
            am.academic_major_title,
            am.academic_major_category_name
        FROM edwa-global.TURBO.S3_TURBO_USER_PROFILE up
        LEFT JOIN edwa-global.TURBO.S3_USER_JOB_SKILL_LINK jsl
            ON up.person_id = jsl.person_id
        LEFT JOIN edwa-global.TURBO.S3_USER_JOB_ROLE_LINK jrl
            ON up.person_id = jrl.person_id
        LEFT JOIN edwa-global.TURBO.S3_USER_EDUCATION_OVERVIEW eo
            ON up.person_id = eo.person_id
        LEFT JOIN edwa-global.TURBO.S3_ACADEMIC_MAJOR am
            ON am.user_academic_major_id = eo.user_academic_major_id
        LEFT JOIN edwa-global.TURBO.S3_JOB_ROLE jr
            ON jr.job_role_id = jrl.job_role_id
        LEFT JOIN edwa-global.TURBO.S3_JOB_SKILL js
            ON jsl.turbo_skill_id = js.turbo_skill_id
        WHERE up.person_id = {}
        """.format('"' + user_id + '"')

        user = self.client.query(query).to_dataframe()  # Make an API request.
        user.columns = [x.lower() for x in user.columns]

        user.rename(columns={
            'skill_title': 'Self-Declared Skills',
            'role_title': 'Preferred Job Roles',
            'academic_major_title': 'Major',
            'academic_major_category_name': 'Major Category',
            'years_until_grad': 'Years until Graduation'
        }, inplace=True)

        # aggregate
        user = user.loc[:, ~user.isna().any(axis=0)].groupby('person_id').agg(lambda x: ", ".join([str(y) for y in set(x)]).rstrip(','))

        return user