import streamlit as st

st.title("Demo Gen AI")


with st.form("my_form"):
    # Create text input boxes
    prompt = st.text_input("Enter your prompt: ")


    # Create a submit button
    submitted = st.form_submit_button("Submit")

    # Display the submitted information
    if submitted:
        import model
        output = model.callGenAI(prompt)
        st.write(output)

