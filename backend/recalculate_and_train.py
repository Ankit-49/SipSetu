from app import create_app
from models import db, Ranking
from ranking_ml import _heuristic_score, train_ranking_model

def main():
    app = create_app()
    with app.app_context():
        rankings = Ranking.query.all()
        count = 0
        for ranking in rankings:
            if ranking.resume and ranking.job:
                new_score = _heuristic_score(ranking.resume, ranking.job)
                ranking.matching_score = new_score
                count += 1
                
        db.session.commit()
        print(f"Updated {count} rankings with new heuristic score.")
        
        print("Training model...")
        result = train_ranking_model()
        print("Train result:", result)

if __name__ == "__main__":
    main()
