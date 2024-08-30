# routes.py
from app import app
from views import home, menucontent, process_draft_results, process_player_info, update_plot, update_outliers, update_recommendations, update_league_info, load_example_auction

def setup_routes():
    app.get("/")(home)
    app.get("/menucontent")(menucontent)
    app.post("/process_draft_results")(process_draft_results)
    app.post("/process_player_info")(process_player_info)
    app.get("/update_plot")(update_plot)
    app.get("/update_outliers")(update_outliers)
    app.get("/update_recommendations")(update_recommendations)
    app.post("/update_league_info")(update_league_info)
    app.post("/load_example_auction")(load_example_auction)