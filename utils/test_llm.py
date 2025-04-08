from google import genai

client = genai.Client(
        #vertexai=True, 
        api_key="AIzaSyCGG8HULh_OLJ_1FwicUtSFv4iDQNzfPZk"
    )
model = "gemini-2.5-pro-exp-03-25"
response = client.models.generate_content(
    model=model,
    contents=['Hello, how are you?']
)
print(response.text)