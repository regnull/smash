#! /usr/bin/env python3

from ollama import chat, ChatResponse
import psutil
import os

import subprocess

model = 'llama3.1'

# Start a shell process
shell = subprocess.Popen(
    "/bin/bash",  # You can replace this with another shell like "/bin/zsh" if desired
    stdin=subprocess.PIPE,
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
    text=True,  # Enable text mode for easier communication
    bufsize=1   # Line-buffered for real-time communication
)

def send_command(command):
    """
    Send a command to the shell and get its output.
    :param command: The shell command to run.
    :return: The command's output as a string.
    """

    if command.get('command'):
        command = command['command']
    elif command.get('cmd'):
        command = command['cmd']


    print(f"\nGenerated command: {command}")
    
    if is_destructive(command):
        while True:
            confirmation = input("Execute? (y/n): ").lower()
            if confirmation == 'y':
                break
            else:
                return "Command execution canceled."
    else:
        print("Command is not destructive. Executing...")

    command = command + " 2>&1"
    print(f"Executing: {command}")
    shell.stdin.write(command + "\n")  # Write the command to the shell
    shell.stdin.write("echo END_OF_COMMAND\n")  # Marker to signify end of the command output
    shell.stdin.flush()  # Ensure the command is processed

    output = []
    while True:
        line = shell.stdout.readline()  # Read the output line by line
        if "END_OF_COMMAND" in line:  # Stop reading once the end marker is encountered
            break
        output.append(line)
    # print("".join(output))
    return "".join(output)

tools=[
    {
        'type': 'function',
        'function': {
            'name': 'send_command',
            'description': 'Send a command to the shell and get its output',
            'parameters': {
                'command': {
                    'type': 'string',
                    'description': 'The command to send to the shell',
                },
            },
        },
    },
]

def is_destructive(command):
    response = chat(
        model,
        messages=[
            {'role': 'system', 'content': f'You are a Linux expert.'},
            {'role': 'user', 'content': f'''Tell me if the following command is destructive: {command}.
A destructive command performs changes in the file system or processes. For example, rm command is destructive.
kill command is destructive. ls command is not destructive. top command is not destructive.
The output must be a single word: "yes" for destructive or "no" for non-destructive. Do not return anything else.
'''}
        ],
    )
    # print(response)
    return response['message']['content'].split()[0].lower() == "yes"

def main():
    conversation_history = [
        {
            'role': 'system', 'content': '''
You are a Linux-based virtual assistant capable of answering questions and executing tasks.

Use tools only when required; otherwise, respond directly or perform the task without tools.
Adapt to conversational tone if the user speaks informally.
If a tool invocation fails, troubleshoot the error and retry. Use resources like man commands for assistance when needed.
Avoid suggesting code-writing techniques; instead, focus on directly solving the user's request.
'''
        }
    ]
    while True:
        user_input = input(">>> ")
        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        conversation_history.append({'role': 'user', 'content': user_input})
        # print(conversation_history)
        response: ChatResponse = chat(
            model,
            messages=conversation_history,
            tools=tools,
            options={
                'temperature': 0.0,
            }
            # stream=True
        )

        while response['message'].get('tool_calls'):
            tool_call = response['message']['tool_calls'][0]
            tool_result = send_command(tool_call['function']['arguments'])
            # print(f"Tool result: {tool_result}")
            conversation_history.append({'role': 'tool', 'content': tool_result})
            response = chat(
                model,
                messages=conversation_history,
                tools=tools,
                options={
                    'temperature': 0.0,
                }
            )

        conversation_history.append({'role': 'assistant', 'content': response['message']['content']})
        print(f"{response['message']['content']}")

if __name__ == "__main__":
    main()
