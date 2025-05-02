from langchain.prompts import ChatPromptTemplate
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from langchain_ollama import ChatOllama 
from colorama import Fore
import asyncio

class Agent:
    def __init__(self, modelName):
        self.modelName = modelName
        self.memory = []
        self.temperature = 0.2
        self.model = ChatOllama(model=self.modelName, base_url="http://localhost:11434", temperature=self.temperature)
        self.instructionsFilename = "SystemInstructions/ConversationInstructions.txt"
        self.systemInstructions = ""
        self.importInstructions()
        self.addToMemory('system', self.systemInstructions)
        
        self.responseTimeout = 60
        
    def importInstructions(self):
        try:
            with open(self.instructionsFilename, 'r') as f:
                self.systemInstructions += f.read()
        except FileNotFoundError:
            print(f"{Fore.RED}Instructions file not found: {self.instructionsFilename}{Fore.RESET}")
            exit(1)
            
    def addToMemory(self, role, content):
        if role == 'system':
            self.memory.append(SystemMessage(content=content))
        elif role == 'user':
            self.memory.append(HumanMessage(content=content))
        elif role == 'assistant':
            self.memory.append(AIMessage(content=content))
        else:
            raise ValueError(f"Unknown role: {role}") 

    async def generateResponseAsync(self, role=None, inputText=None): # Generate response based on input
        try:
            if inputText and role:
                self.addToMemory(role, inputText)
                
            history = ChatPromptTemplate.from_messages(self.memory)
            chain = history | self.model
            response = await chain.ainvoke({})
            response_content = response.content if isinstance(response, AIMessage) else response
            self.addToMemory('assistant', response_content)
            return response_content.strip()
        except Exception as e:
            print(f"Error generating response: {e}")
            exit(1)
        
    def generateResponse(self, role=None, inputText=None): # Generate response based on input
        try:
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                asyncio.wait_for(
                    self.generateResponseAsync(role, inputText),
                    timeout = self.responseTimeout
                    )
                )
            return response
        except asyncio.TimeoutError:
            print(f"{Fore.RED}Timeout error while generating response for Agent{Fore.RESET}")
            exit(1)
            
    def printMemory(self):
        print(f"----------------Agent's Memory:{Fore.RESET}----------------")
        for i, message in enumerate(self.memory):
            # if i == 0: # Skip the system message
            #     continue
            if isinstance(message, SystemMessage):
                print(f"{Fore.LIGHTRED_EX}System: {message.content}{Fore.RESET}")
            elif isinstance(message, HumanMessage):
                print(f"{Fore.LIGHTGREEN_EX}Partner: {message.content}{Fore.RESET}")
            elif isinstance(message, AIMessage):
                print(f"{Fore.LIGHTBLUE_EX}Agent: {message.content}{Fore.RESET}")
            else:
                print(f"Unknown message type: {message}")
            print("----------------------------------------------------------------------------------------")
        print(f"----------------{Fore.LIGHTYELLOW_EX}END Memory:{Fore.RESET}----------------")