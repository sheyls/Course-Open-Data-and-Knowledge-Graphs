import traceback

import streamlit as st
from rdflib import Graph
import os
from wikidata_query import *
from wikidata_query import *

# Set as currently used name of the RDF file
rdf_file = "subset-graph-updated.ttl"
# Layout with columns
left_col, center_col, right_col = st.columns(3)

file_directory = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
parent_directory = os.path.abspath(os.path.join(file_directory, '..'))
image_path = os.path.join(parent_directory, 'src', 'bicimad.png')
rdf_path = os.path.join(parent_directory, 'rdf', rdf_file)
pickle_path = os.path.join(parent_directory, 'rdf', 'bike_graph.pkl')

if __name__ == "__main__":
    with center_col:
        st.image(image_path, width=130)

    # Title of the application
    st.title("BiciMAP: Analyzing BiciMAD Data Using RDF")

    # Load the Turtle file as a database
    @st.cache_resource
    def load_bike_graph():
        g = Graph()
        try:
            # Load the Turtle file from a specific path
            if os.path.exists(pickle_path):
                print("Loading from pkl...")
                with open(pickle_path, 'rb') as f:
                    g = pickle.load(f)
            else:
                g.parse(rdf_path, format="turtle")
                with open(pickle_path, 'wb') as f:
                    pickle.dump(g, f)

            st.sidebar.write("Turtle file loaded successfully.")
        except Exception as e:
            st.sidebar.error(f"Error loading the Turtle file: {e}")
        return g

    # Initialize the graph
    graph = load_bike_graph()
    # Display general information about the graph in the sidebar
    st.sidebar.write(f"The graph contains {len(graph)} triples.")

    # Section for SPARQL queries in the sidebar
    st.sidebar.subheader("Annotator")
    category = st.sidebar.text_area(
        "WikiData class:",
        value="""Q875538""",
        height=20,
    )
    limit = st.sidebar.text_area(
        "Limit of WikiData entities collected:",
        value="""10""",
        height=20,
    )
    max_distance = st.sidebar.text_area(
        "Distance threshold (km):",
        value="""0.1""",
        height=20,
    )
    out_file = st.sidebar.text_area(
        "Name of output file:",
        value="""output.ttl""",
        height=20,
    )

    # Button in the sidebar to execute the query
    if st.sidebar.button("Run annotator"):
        try:
            # Execute the SPARQL query
            print(f"The output will be found at: {os.path.join(parent_directory, 'app', out_file)}")
            annotate_category(bike_graph=graph, category=category, limit=int(limit), max_dist=float(max_distance), out=os.path.join(parent_directory, 'app', out_file))

            # Display the results in a table if there is data
            st.subheader("Annotation successful.")
        except Exception as e:
            st.error(f"Execution error: {e}")
            st.error(traceback.format_exc())
