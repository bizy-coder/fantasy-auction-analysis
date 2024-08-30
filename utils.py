from fasthtml.common import *

# def scrollable_table_style():
# 	return Style("""
# 		.table-scrollable {
# 			max-height: 400px;
# 			overflow-y: auto;
# 			overflow-x: auto;
# 			border: 1px solid #dee2e6;
# 			padding-right: 15px; /* Added padding to ensure room for the border */
# 			margin-right: -15px; /* Compensate for added padding to avoid horizontal overflow */
# 		}
# 		.table-scrollable table {
# 			margin-bottom: 0;
# 			width: 100%;
# 		}
# 		.table-scrollable thead th {
# 			position: sticky;
# 			top: 0;
# 			background-color: #f8f9fa;
# 			z-index: 1;
# 		}
# 	""")
 
def scrollable_table_style():
    return Style("""
		.table-scrollable {
			max-height: 400px;
			overflow-y: auto;
			overflow-x: auto;
			border: 1px solid #dee2e6;
			padding-right: 15px; /* Added padding to ensure room for the border */
			margin-right: -15px; /* Compensate for added padding to avoid horizontal overflow */
		}
		.table-scrollable table {
			margin-bottom: 0;
			width: 100%;
		}
		.table-scrollable thead th {
			position: sticky;
			top: 0;
			background-color: #f8f9fa;
			z-index: 1;
		}
  
        .card {
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            transition: all 0.3s ease;
        }
        .card:hover {
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }
        .card-body {
            padding: 1rem;
        }
        .card-title {
            border-bottom: 2px solid;
            padding-bottom: 0.5rem;
            margin-bottom: 1rem;
        }
        .table-sm {
            font-size: 0.9rem;
        }
        .fw-bold {
            font-weight: 600;
        }
        
        .player-card {
            border: 1px solid #dee2e6;
            border-radius: 0.25rem;
            padding: 0.5rem;
            margin-bottom: 0.5rem;
            background-color: #f8f9fa;
        }
        .player-name {
            font-weight: bold;
            margin-bottom: 0.25rem;
        }
        .player-team, .player-proj, .player-price {
            font-size: 0.9rem;
        }
        .trade-details {
            border-left: 4px;
            padding: 0.5rem 1rem;
            margin-bottom: 1rem;
        }
    """)

def get_starter_quality_threshold(df, position):
    starters = df[(df['Position'] == position) & (df['Starter'] == 'Starter')]
    return starters['Projected_Points'].min()