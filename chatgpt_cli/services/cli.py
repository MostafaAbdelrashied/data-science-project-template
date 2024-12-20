import os

from chatgpt_cli.repositories import ChatRepository, MessageRepository, UserRepository
from chatgpt_cli.models import Chat, Message, User
from chatgpt_cli.llm.openai_client import OpenAIClient


class ChatService:
    def __init__(self, read_file: str = None, stream: bool = False):
        self.user_repository = UserRepository()
        self.chat_repository = ChatRepository()
        self.message_repository = MessageRepository()
        self.client = OpenAIClient(stream)
        self.read_file_content = (
            self.load_file_content(read_file) if read_file else None
        )

    def load_file_content(self, file_path: str) -> str:
        if not file_path:
            return None
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            return None
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    async def start(self):
        print("Welcome to the OpenAI Chat Interface!")
        username = input("Enter your username: ").strip()

        # The repositories manage sessions internally
        user = await self.user_repository.get_user_by_username(username)
        if not user:
            user = User(username=username)
            await self.user_repository.create_user(user)

        while True:
            print("\nOptions:")
            print("1. Start a new chat")
            print("2. Continue a previous chat")
            print("3. Exit")
            choice = input("Select an option: ").strip()
            if choice == "1":
                model_name = await self.select_model()
                if model_name:
                    await self.new_chat(user, model_name)
            elif choice == "2":
                model_name = await self.select_model()
                if model_name:
                    await self.continue_chat(user, model_name)
            elif choice == "3":
                print("\nGoodbye!")
                break
            else:
                print("Invalid choice. Please try again.")

    async def select_model(self):
        models = await self.client.list_models()
        if not models:
            print("No models available.")
            return None
        print("\nSelect a model to chat with:")
        for idx, model in enumerate(models, 1):
            print(f"{idx}. {model.id}")
        choice = input("Enter model number: ").strip()
        try:
            model_index = int(choice) - 1
            if 0 <= model_index < len(models):
                model_name = models[model_index].id
                if ("o1" in model_name) and self.client.stream:
                    print("+-----------------------------------------------------------------------------------+")
                    print("+---Streaming is not supported for the o1 models. Switching to non-streaming mode---+")
                    print("+-----------------------------------------------------------------------------------+")
                    self.client.stream = False
                return model_name
            else:
                print("Invalid selection.")
                return None
        except ValueError:
            print("Please enter a valid number.")
            return None

    async def new_chat(self, user: User, model_name: str):
        chat = Chat(user_id=user.id)
        await self.chat_repository.create_chat(chat)
        await self.chat_loop(chat, model_name)

    async def continue_chat(self, user: User, model_name: str):
        chats = await self.chat_repository.get_chats_by_user(user.id)
        if not chats:
            print("\nNo previous chats found.")
            return
        print("\nPrevious chats:")
        for idx, chat in enumerate(chats, 1):
            print(f"{idx}. Chat ID: {chat.id}, Created At: {chat.created_at}")
        choice = input("Enter the chat number to continue: ").strip()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(chats):
                chat = chats[idx]
                await self.chat_loop(chat, model_name)
            else:
                print("Invalid selection.")
        except ValueError:
            print("Please enter a valid number.")

    async def chat_loop(self, chat: Chat, model_name: str):
        print(f"\nChatting with model: {model_name}. Type 'exit' to end the chat.\n")
        conversation = []

        # Fetch messages without managing sessions here
        messages = await self.message_repository.get_messages_by_chat(chat.id)
        for message in messages:
            conversation.append({"role": message.sender, "content": message.content})
            print(f"{message.sender.capitalize()}: {message.content}")

        # If there's file content, add it as a user message at the start
        if self.read_file_content:
            print("Adding file content to chat.")
            conversation.append({"role": "user", "content": self.read_file_content})
            message = Message(
                chat_id=chat.id, sender="user", content=self.read_file_content
            )
            await self.message_repository.create_message(message)
            self.read_file_content = None

        while True:
            user_input = input("You: ").strip()
            if user_input.lower() == "exit":
                print("Ending the chat.")
                break
            conversation.append({"role": "user", "content": user_input})
            message = Message(chat_id=chat.id, sender="user", content=user_input)
            await self.message_repository.create_message(message)

            response_text = await self.client.get_response(
                model_name=model_name, messages=conversation
            )
            conversation.append({"role": "assistant", "content": response_text})
            message = Message(
                chat_id=chat.id,
                sender="assistant",
                content=response_text,
                model=model_name,
            )
            await self.message_repository.create_message(message)
