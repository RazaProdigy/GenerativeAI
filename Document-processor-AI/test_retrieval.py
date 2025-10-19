from vector_store import retrieve_with_score

query = "What is Generative  AI?"

print("Query: ", query)

results = retrieve_with_score(query)

if not results:
    print("No results found")
else:
    for i, (doc, score) in enumerate(results):
        print(f"Result {i+1}:")
        print(f"Score: {score}")
        print(f"Document: {doc}")
        print("-"*100)