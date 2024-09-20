from pinecone.grpc import PineconeGRPC as Pinecone
import os
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
import time
from langchain.chains import RetrievalQA  
from langchain_openai import ChatOpenAI


class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


pc = Pinecone(api_key=os.environ.get("PINECONE_API_KEY"))

chat_manager = None

def start_chunking(place_info):


    chunks = []
    for place in place_info:
        # Place-level chunk
        place_chunk = Document(
            page_content=f"Place Name: {place['place_name']}\n"
                        f"Average Rating: {place['average_rating']}\n"
                        f"Total Reviews: {place['total_reviews']}",
            metadata={
                "chunk_type": "place_info",
                "place_name": place["place_name"],
                "average_rating": place["average_rating"],
                "total_reviews": place["total_reviews"]
            }
        )
        chunks.append(place_chunk)
        
        # Review-level chunks
        for review in place["reviews"]:
            review_chunk = Document(
                page_content=f"Review Rating: {review['rating']}\n"
                            f"Review Text: {review['review_text']}\n"
                            f"Published At: {review['published_at']}\n"
                            f"Published At Date: {review['published_at_date']}\n"
                            f"Review Likes Count: {review['review_likes_count']}\n"
                            f"Total Number of Reviews by Reviewer: {review['total_number_of_reviews_by_reviewer']}\n"
                            f"Is Local Guide: {review['is_local_guide']}",
                metadata={
                    "chunk_type": "review",
                    "name_of_place": place["place_name"],
                    "review_rating": review["rating"],
                    "review_text": review["review_text"],
                    "review_published_at": review["published_at"],
                    "review_published_at_date": review["published_at_date"],
                    "review_likes_count": review["review_likes_count"],
                    "total_number_of_reviews_by_reviewer": review["total_number_of_reviews_by_reviewer"],
                    "is_local_guide": review["is_local_guide"]
                }
            )
            chunks.append(review_chunk)
    
    model_name = "text-embedding-3-small"  
    embeddings = OpenAIEmbeddings(
        model=model_name,
        openai_api_key=os.environ.get("OPENAI_API_KEY")
    )


    docsearch = PineconeVectorStore.from_documents(
    documents= chunks,
    index_name="reviews",
    embedding=embeddings, 
    namespace= place["place_name"],
    )

    # Wait for the embeddings to be indexed
    time.sleep(1)
    
class ChatManager:
    def __init__(self, model_name="gpt-3.5-turbo", temperature=0.0, max_tokens=1000):
        self.llm = ChatOpenAI(
            openai_api_key=os.environ.get("OPENAI_API_KEY"),
            model_name=model_name,
            temperature=temperature
        )
        self.max_tokens = max_tokens
        self.chat_history = []
        self.system_context = f"You are Google places AI assistant. You have access to reviews and provide users with insights using the reviews.\
               Keep the responses consise. Format the responses for easier readability."
        self.initialize()

    def initialize(self):
        # Add the system context to the chat history
        self.chat_history.append({"role": "system", "content": self.system_context})

    def add_message(self, role, content):
        self.chat_history.append({"role": role, "content": content})
        self.truncate_history()

    def truncate_history(self):
        # Ensure the total token count is within limits
        total_tokens = self.calculate_total_tokens()
        while total_tokens > self.max_tokens:
            self.chat_history.pop(1)  # Remove the oldest user message
            total_tokens = self.calculate_total_tokens()

    def calculate_total_tokens(self):
        # Approximate token calculation: Each word is about 1.3 tokens on average
        total_tokens = sum(len(msg['content'].split()) * 1.3 for msg in self.chat_history)
        return total_tokens

    def get_prompt(self):
        return "\n".join(f"{msg['role']}: {msg['content']}" for msg in self.chat_history)

def get_inference(query, place_name):
    # Initialize a LangChain object for retrieving information from Pinecone.
    global chat_manager
    knowledge = PineconeVectorStore.from_existing_index(
        index_name="reviews",
        namespace=place_name,
        embedding=OpenAIEmbeddings(openai_api_key=os.environ["OPENAI_API_KEY"])
    )

    
   

    # Create a prompt incorporating chat history
    prompt = chat_manager.get_prompt()


    # Retrieve relevant reviews
    retrieved_reviews = knowledge.similarity_search(query= query, k=10)



    # Combine the retrieved reviews into a single string
    retrieved_reviews_content = "\n\n".join(doc.page_content for doc in retrieved_reviews)

    # Add the retrieved reviews to the prompt
    full_prompt = f"""Here is the chat history: {prompt}\n\n
     Here are the relevant reviews based on user query: {retrieved_reviews_content} \n\n
     Based on the reviews and context from the chat history,  respond to this users query: {query}
        Give very specific responses that help users gain insights into the place."""

    # Get the model response
    answer = chat_manager.llm.invoke(full_prompt).content


     # Add the current user query to the chat history
    chat_manager.add_message("user", query)

    # Update chat history with the assistant's response
    chat_manager.add_message("assistant", answer)

 
    return answer

def isDatavectorized(place_name):

    index = pc.Index("reviews")
    results = index.list_paginated(
    limit=5,
    namespace=place_name
    )
    if len(results.vectors) == 0:
        print("Data not vectorized")
        return False
    else:
        print("Data vectorized")
        return True




