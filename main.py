from agent import Agent
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

class Conversation:
    def __init__(self):
        self.model = "llama3.1:8b"
        self.host = Agent(self.model)

    def start_chat(self):
        print(f"{Fore.YELLOW}Starting conversation with {self.model}. Type 'quit' to exit.{Fore.RESET}")
        
        # Initial greeting from the agent
        initial_response = self.host.generateResponse(inputText="Greet the user.")
        print(f"{Fore.LIGHTBLUE_EX}Agent: {initial_response}{Fore.RESET}")

        while True:
            user_input = input(f"{Fore.LIGHTGREEN_EX}You: {Fore.RESET}")
            if user_input.lower() == 'quit':
                print(f"{Fore.YELLOW}Ending conversation.{Fore.RESET}")
                # Print agent's memory before exiting
                # self.host.printMemory()
                self.host.save_agent_profile() # Save the profile on quit
                break

            if user_input:
                agent_response = self.host.generateResponse(role='user', inputText=user_input)
                print(f"{Fore.LIGHTBLUE_EX}Agent: {agent_response}{Fore.RESET}")
            else:
                print(f"{Fore.RED}Please enter some text.{Fore.RESET}")

if __name__ == "__main__":
    conversation = Conversation()
    conversation.start_chat()
