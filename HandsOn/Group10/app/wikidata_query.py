import os
import pickle

import numpy as np
from geopy.distance import geodesic
from SPARQLWrapper import SPARQLWrapper, JSON, CSV
import pandas as pd
from rdflib import Graph, URIRef, Literal, Namespace
from rdflib.namespace import RDF, RDFS, XSD

TYPES_OF_INTEREST = {
    # "hospital": "Q16917",
    # "shopping center": "Q11315",
    "educational institution": "Q2385804",
    # "public transport stop": "Q548662",
    # "park": "Q22698",
    # "square": "Q174782",
    # "sports venue": "Q1076486",
}


def _query_places(queried_class, limit: int = 10):
    sparql = SPARQLWrapper("https://query.wikidata.org/sparql")

    # From https://www.wikidata.org/wiki/Wikidata:SPARQL_query_service/queries/examples#Cats
    query = """
    SELECT DISTINCT ?item ?itemLabel ?latitude ?longitude 
    WHERE
    {   
        ?instance wdt:P279* wd:""" + queried_class + """.  # Instances of subclasses of the queried class
        ?item wdt:P31 ?instance.
        ?item wdt:P625 ?coordinate. # Get the coordinates
        ?item wdt:P131 wd:Q2807.  # Ensuring the item is located in Madrid 
        BIND(geof:latitude(?coordinate) AS ?latitude).
        BIND(geof:longitude(?coordinate) AS ?longitude).
        SERVICE wikibase:label { bd:serviceParam wikibase:language "en" }
    }
    LIMIT """ + str(round(limit)) + """
    """
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    results_df = pd.json_normalize(results['results']['bindings'])

    df = pd.DataFrame()
    df['subject'] = results_df['item.value']
    df['label'] = results_df['itemLabel.value']
    df['latitude'] = results_df['latitude.value'].astype(float)
    df['longitude'] = results_df['longitude.value'].astype(float)

    return df


def query_places_as_graph(queried_class="Q2385804", limit=10):
    print(f"Getting all entities subclass of {queried_class}")
    df = _query_places(queried_class, limit=limit)
    # Create an RDF graph
    g = Graph()

    # Define namespaces
    GEO = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")

    # Add each row in the DataFrame to the RDF graph
    for _, row in df.iterrows():
        item_uri = URIRef(row['subject'])
        g.add((item_uri, RDF.type, URIRef("http://www.wikidata.org/entity/" + queried_class)))
        # g.add((item_uri, RDF.subClassOf, SCHEMA.Place))  # Define the item as a place
        g.add((item_uri, RDFS.label, Literal(row['label'], lang="en")))
        g.add((item_uri, GEO.lat, Literal(row['latitude'], datatype=XSD.float)))
        g.add((item_uri, GEO.long, Literal(row['longitude'], datatype=XSD.float)))

    return g


def get_all_places_of_interest():
    accum = Graph()
    for name, place in TYPES_OF_INTEREST.items():
        print(f"Querying for {name}", end="")
        accum += query_places_as_graph(place)
        print(f"\rCompleted queries for {name}")
    return accum


def get_distance(coords_1, coords_2):
    return geodesic(coords_1, coords_2).km


def join_by_distance(bike_graph, wikidata_graph, max_distance=0.1, debug=False):
    """
    Increases the graph given to now add places in the wikidata graph and gives them the relationship
    geo:Touches with BikeStation's based on the maximim distance used as threshold and returns the new graph

    :param bike_graph: bike graph
    :param wikidata_graph: graph of wikidata places
    :param max_distance: max dist tolerated to be considered geo:Touches
    :return:
    """
    g = bike_graph
    g += wikidata_graph

    ns1 = Namespace("https://BiciMad.es/ontology#")
    schema = Namespace("https://schema.org/")
    geo = Namespace("http://www.w3.org/2003/01/geo/wgs84_pos#")
    wikidata = Namespace("http://www.wikidata.org/entity/")

    if debug:
        query = """
                SELECT ?place ?latitude ?longitude
                WHERE {
                    ?place a ns1:BikeStation  ;
                           schema:latitude ?latitude ;
                           schema:longitude ?longitude .
                }
                """

        out1 = g.query(query, initNs={"ns1": ns1, "schema": schema, "geo": geo, "wikidata": wikidata})
        # Execute the query
        out1.serialize(format='csv', destination='output5.1.csv')
        print("Done 5.1")

        query = """
                SELECT ?class ?point ?latitude2 ?longitude2
                WHERE {
                    ?point geo:lat ?latitude2 ;
                           geo:long ?longitude2 ;
                           a ?class .
                }
                """

        out1 = g.query(query, initNs={"ns1": ns1, "schema": schema, "geo": geo, "wikidata": wikidata})
        # Execute the query
        out1.serialize(format='csv', destination='output5.2.csv')
        print("Done 5.2")

    query = """
        SELECT ?place ?latitude ?longitude ?class ?point ?latitude2 ?longitude2 
        WHERE {
            ?place a ns1:BikeStation  ;
                   schema:latitude ?latitude ;
                   schema:longitude ?longitude .
                   
            ?point geo:lat ?latitude2 ;
                   geo:long ?longitude2 ;
                   a ?class .
        }
        """

    print("Running queries...")
    out1 = g.query(query, initNs={"ns1": ns1, "schema": schema, "geo": geo, "wikidata": wikidata})
    # Execute the query
    if debug:
        out1.serialize(format='csv', destination='output5.csv')
        print("Done 5")

    print("All coordinates found...")
    print("Annotating...", end="")
    for row in out1:
        coord1 = (row['latitude'], row['longitude'])
        coord2 = (row['latitude2'], row['longitude2'])
        dist = get_distance(coord1, coord2)
        if dist < max_distance:
            g.add(row['place'], geo.Touches, row['point'])

    print("\rAnnotation complete.")
    return g


def annotate_category(bike_graph, category="Q2385804", max_dist=0.1, limit=10, out="./output.ttl"):
    """
    Increases the graph given to now add places in Madrid under the category of WikiData and gives them the relationship
    geo:Touches with BikeStation's based on the maximim distance used as threshold and prints it out as a ttl.
    :param bike_graph: rdflib graph containing the BikeStation's
    :param category: category of wikidata, given as a string e.g. "Q2385804"
    :param max_dist: max distance in KM
    :param out: out file path
    :return:
    """
    print(category, max_dist, limit, out)
    wikidata_graph = query_places_as_graph(category, limit=limit)
    g = join_by_distance(bike_graph, wikidata_graph, max_distance=max_dist)
    g.serialize(out, format='turtle')


if __name__ == '__main__':
    # Set as currently used name of the RDF file
    rdf_file = "subset-graph-updated.ttl"

    file_directory = os.path.abspath(os.path.join(os.path.abspath(__file__), '..'))
    parent_directory = os.path.abspath(os.path.join(file_directory, '..'))
    rdf_path = os.path.join(parent_directory, 'rdf', rdf_file)

    pickle_path = os.path.join(parent_directory, 'rdf', 'bike_graph.pkl')

    # Check if the Pickle file exists (i.e., previously serialized)
    if os.path.exists(pickle_path):
        print("Loading from pkl...")
        with open(pickle_path, 'rb') as f:
            bike_graph = pickle.load(f)
    else:
        bike_graph = Graph()
        bike_graph.parse(rdf_path, format="turtle")
        with open(pickle_path, 'wb') as f:
            pickle.dump(bike_graph, f)

    wikidata_graph = get_all_places_of_interest()

    graph = join_by_distance(bike_graph, wikidata_graph)
    print(graph)
