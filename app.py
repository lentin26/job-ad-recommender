from flask import Flask, jsonify, request
from src.models.RatingMatch import load_model
from src.inference.VectorSearch import VectorSearch
from src.preprocess.ValueEncoder import ValueEncoder

DB_PATH = 'data/db_vectors.csv' # = os.getenv(DB_PATH)
MODEL_PATH = 'models/v1/ratingmatch.json'  # = os.getenv(MODEL_PATH)
ENCODER_PATH = 'models/v1/encoder.json'  # = os.getenv(ENCODER_PATH)

app = Flask(__name__)

@app.route("/job_ad/recommend", methods = ['POST'])
def recommend():
    """
    Recommend job ad given covariates. Request form:
    {
        "turbo_skill_id": [],           # user self-declared skills, change to feathm_skill_id
        "job_role_id": [],              # user job role preferences (Faethm occupational codes) 
        "years_until_grad": [],         # change to user_grade (e.g., freshman, graduate, etc.)
        "school_id": [],                # from Turbo
        "user_academic_major_id": []    # from Turbo
        "job_ad_ids": []                # list of clicked (bookmark, apply, details) jobs
    }
    """
    # get data
    r = request.get_json()
    datapoint = list(r.values())

    # encode datapoint
    encoder = ValueEncoder(ENCODER_PATH)
    datapoint = encoder.encode([datapoint])[0]

    # load pretrained model, embbed user datapoint
    match = load_model(MODEL_PATH=MODEL_PATH)
    query = match.predict_proba(datapoint, burn_in=10)

    # instantiate search, get recommendations
    search = VectorSearch(DB_PATH=DB_PATH)
    job_ids, scores = search.search(query, n=5)

    # return recommendations
    response = {
        'job_id': job_ids,
        'score': scores
    }
    return jsonify(response)

######### add in Thompson sampling #########
# Only sample for users, keep items fixed. Store covariance matrix and vector
# not sure if it makes sense to hit RatingMatch in realtime or store vectors
# and update with TS. TS is memoryless, so if a user updates params we cannot
# backpropagate
# or we could use clicked jobs in the payload for RatingMatch?

#  Curl -X POST -H "Content-Type: application/json" -d '{"turbo_skill_id": [], "job_role_id": [235, 53, 54, 56, 57, 59, 61, 62], "years_until_grad": [], "school_id": [486], "user_academic_major_id": [16]}' http://127.0.0.1:5000/job_ad/recommend
#  Curl -X POST -H "Content-Type: application/json" -d '{"turbo_skill_id": [], "job_role_id": ["a9d5e", "a17db"], "years_until_grad": [], "school_id": [], "user_academic_major_id": ["6ff04"]}' http://127.0.0.1:5000/job_ad/recommend

if __name__ == '__main__':
    app.run()