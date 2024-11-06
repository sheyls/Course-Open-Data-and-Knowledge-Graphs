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
            g.parse(rdf_path, format="turtle")  # Make sure the path is correct
            st.sidebar.write("Turtle file loaded successfully.")
        except Exception as e:
            st.sidebar.error(f"Error loading the Turtle file: {e}")
        return g


    @st.cache_resource
    def load_places_of_interest():
        g = Graph()
        try:
            # Load the Turtle file from a specific path
            g = get_all_places_of_interest()# Make sure the path is correct
            st.sidebar.write("Queries ran successfully.")
        except Exception as e:
            st.sidebar.error(f"Error running queries: {e}")
        return g

    # Initialize the graph
    graph = load_bike_graph()
    # Display general information about the graph in the sidebar
    st.sidebar.write(f"The graph contains {len(graph)} triples.")

    # Section for SPARQL queries in the sidebar
    st.sidebar.subheader("SPARQL Query")
    category = st.sidebar.text_area(
        "Write the WikiData class here:",
        value="""
        Q875538
        """,
        height=300,
    )

    # Button in the sidebar to execute the query
    if st.sidebar.button("Run annotator"):
        try:
            # Execute the SPARQL query
            graph.query(category)

            # Display the results in a table if there is data
            st.subheader("Annotation successful.")
        except Exception as e:
            st.error(f"Execution error: {e}")
