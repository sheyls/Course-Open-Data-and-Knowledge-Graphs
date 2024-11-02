import streamlit as st
from rdflib import Graph

# Layout with columns
left_col, center_col, right_col = st.columns(3)
with center_col:
    st.image('../src/bicimad.png', width=130)

# Title of the application
st.title("BiciMAP: Analyzing BiciMAD Data Using RDF")

# Load the Turtle file as a database
@st.cache_resource
def load_graph():
    g = Graph()
    try:
        # Load the Turtle file from a specific path
        g.parse("bicimap_data.ttl", format="turtle")  # Make sure the path is correct
        st.sidebar.write("Turtle file loaded successfully.")
    except Exception as e:
        st.sidebar.error(f"Error loading the Turtle file: {e}")
    return g

# Initialize the graph
graph = load_graph()

# Display general information about the graph in the sidebar
st.sidebar.write(f"The graph contains {len(graph)} triples.")

# Section for SPARQL queries in the sidebar
st.sidebar.subheader("SPARQL Query")
query = st.sidebar.text_area(
    "Write your SPARQL query here:",
    value="""
    SELECT ?subject ?predicate ?object
    WHERE {
        ?subject ?predicate ?object .
    }
    LIMIT 10
    """,
    height=300,
)

# Button in the sidebar to execute the query
if st.sidebar.button("Run Query"):
    try:
        # Execute the SPARQL query
        results = graph.query(query)
        
        # Create a list to store the results
        data = []
        for row in results:
            # Show only the end of the URI or text, not the full link
            data.append([str(cell).split('/')[-1] for cell in row])  
        
        # Display the results in a table if there is data
        if data:
            st.subheader("Query Results:")
            st.table(data)
        else:
            st.write("No results found for the query.")
    except Exception as e:
        st.error(f"Query error: {e}")
