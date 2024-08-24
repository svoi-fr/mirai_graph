from neo4j import GraphDatabase
import openpyxl
import json
from FlagEmbedding import BGEM3FlagModel

import os

EXCEL_FILE_PATH = "output.xlsx"
NEO4J_URI = os.environ.get("NEO4J_URI", "bolt://localhost:7687")  # Get from environment or default
NEO4J_PASSWORD = os.environ.get("NEO4J_PASSWORD")  # Get from environment
NEO4J_USER = "neo4j"
BATCH_SIZE = 100  # Adjust the batch size as needed

# Initialize the BAAI BGE M3 embedding model
model = BGEM3FlagModel('BAAI/bge-m3', use_fp16=True)

def create_neo4j_nodes_and_relationships(excel_file_path, neo4j_uri, neo4j_user, neo4j_password):
    """Creates Neo4j nodes, relationships, and embeddings from Excel data."""

    driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    wb = openpyxl.load_workbook(excel_file_path)
    ws_data = wb["LLM Responses"]

    with driver.session() as session:
        for row in ws_data.iter_rows(min_row=2):  # Skip header row
            url, _, response_cell = row
            url = url.value
            response_json = json.loads(response_cell.value)

            # --- Create Document node and embedding ---
            summary = response_json["Summary"]
            document_embedding = model.encode(summary.get("description", ""))
            session.run(
                """
                MERGE (d:Document {id: $summary_id})
                SET d.country = $country,
                    d.description = $description,
                    d.type = $type,
                    d.url = $url,
                    d.embedding = $embedding
                """,
                summary_id=summary["id"],
                country=summary["country"],
                description=summary.get("description", ""),
                type=summary["type"],
                url=url,
                embedding=list(document_embedding)
            )

            # --- Create other nodes and relationships in batches ---
            for node_type in ["Context", "Provision", "Task", "Organization", "Contact"]:
                nodes = response_json.get(node_type, [])
                for i in range(0, len(nodes), BATCH_SIZE):
                    batch_nodes = nodes[i:i + BATCH_SIZE]
                    info_texts = [node.get("info", "") for node in batch_nodes]
                    embeddings = model.encode(info_texts)

                    # Create nodes and relationships in batch
                    for node, embedding in zip(batch_nodes, embeddings):
                        node_id = node["id"]
                        node_label = node_type

                        # --- Merge node (create or update) ---
                        session.run(
                            f"""
                            MERGE (n:{node_label} {{id: $node_id}})
                            ON CREATE SET n.info = $info, n.embedding = $embedding
                            ON MATCH SET 
                                n.info = CASE WHEN $info <> '' THEN coalesce(n.info, $info) ELSE n.info END,
                                n.url = CASE WHEN $url <> '' THEN coalesce(n.url, $url) ELSE n.url END,
                                n.phone = CASE WHEN $phone <> '' THEN coalesce(n.phone, $phone) ELSE n.phone END,
                                n.email = CASE WHEN $email <> '' THEN coalesce(n.email, $email) ELSE n.email END,
                                n.address = CASE WHEN $address <> '' THEN coalesce(n.address, $address) ELSE n.address END,
                                n.city = CASE WHEN $city <> '' THEN coalesce(n.city, $city) ELSE n.city END,
                                n.embedding = CASE WHEN $embedding <> [] THEN coalesce(n.embedding, $embedding) ELSE n.embedding END
                            WITH n, $cities AS new_cities
                            UNWIND new_cities AS new_city
                            MERGE (n)-[:IN_CITY]->(city:City {{name: new_city}})
                            """,
                            node_id=node_id,
                            info=node.get("info", ""),
                            url=node.get("url", ""),
                            phone=node.get("phone", ""),
                            email=node.get("email", ""),
                            address=node.get("address", ""),
                            city=node.get("city", ""),
                            cities=node.get("cities", []),
                            embedding=list(embedding)
                        )

                        # --- Create relationships (same as before) ---
                        for ref_type in ["contexts", "provision", "organizations", "contacts"]:
                            for ref_id in node.get(ref_type, []):
                                ref_label = ref_type[:-1].capitalize()
                                session.run(
                                    f"""
                                    MATCH (source:{node_label} {{id: $node_id}}), (target:{ref_label} {{id: $ref_id}})
                                    MERGE (source)-[:HAS_{ref_label.upper()}]->(target)
                                    """,
                                    node_id=node_id,
                                    ref_id=ref_id
                                )

    driver.close()
    print("Neo4j nodes, relationships, and embeddings created successfully!")

if __name__ == "__main__":
    create_neo4j_nodes_and_relationships(EXCEL_FILE_PATH, NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)