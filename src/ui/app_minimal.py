"""Minimal test version of the UI."""
import gradio as gr

print("Creating minimal interface...")

def create_interface():
    with gr.Blocks(title="RAG Chatbot - Test") as app:
        gr.Markdown("# Test Interface")

        with gr.Tabs():
            with gr.Tab("Chat"):
                gr.Markdown("Chat tab")

        print("Interface created successfully")

    return app

if __name__ == "__main__":
    print("Testing standalone...")
    app = create_interface()
    print("Launching...")
    app.launch(share=False, server_name="127.0.0.1")
