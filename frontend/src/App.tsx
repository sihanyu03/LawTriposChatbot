import { useState } from 'react'
import {askConfluence} from "./api/axios";
import Typewriter from "react-typewriter-effect";
import './index.css'

interface Message {
    context: Map<string, number> | undefined
    text: string | undefined
    isUser: boolean
}

function App() {
    const [input, setInput] = useState<string>("");
    const [isLoading, setIsLoading] = useState(false);
    const [messages, setMessages] = useState<Message[]>([
        {
            context: undefined,
            text: "Example user message message message message message message message message message message message",
            isUser: true
        },
        {
            context: new Map([["File1", 1], ["File2", 2]]),
            text: "Example AI message message message message message message message message message message message message",
            isUser: false
        },
        {
            context: undefined,
            text: "Example user message 2",
            isUser: true
        },
        {
            context: new Map([["File98", 10], ["File64", 976]]),
            text: "Example AI message 2message message message message message message message message message message message messagemessage message message message message message message message message message message messagemessage message message message message message message message message message message messagemessage message message message message message message message message message message message",
            isUser: false
        }
    ])

    const sendMessage = async() => {
        if (input.trim() === "") {
            return;
        }
        setIsLoading(true);
        const response = await askConfluence(input);
        setMessages([
            ...messages,
            {context: undefined, text: input, isUser: true},
            {context: response?.context, text: response?.text, isUser: false}
        ])
        setInput("");
        setIsLoading(false);
    }

    return (
        <div className="flex flex-col h-[100vh] w-[100vw] bg-gray-950 text-white">
            <div className="flex-grow overflow-y-auto p-4 space-y-4">
                {messages.map((message) => (
                    <div className={`flex flex-col space-y-4 ${message.isUser ? "justify-end" : "justify-start"}`}>
                        {!message.isUser && message.context != undefined ? (
                            <div className={"p-3 rounded-2xl break-words max-w-[80%] bg-gray-700 text-white self-start"}>
                                <div>Context:</div>
                                <div>{Array.from(message.context).map(([file, page]) => (
                                    <Typewriter text={`File: ${file}, Page: ${page}`} typeSpeed={5} cursorColor="transparent" />
                                ))}</div>
                            </div>
                        ) : null}
                        <div className={`p-3 rounded-2xl break-words max-w-[80%] ${
                            message.isUser ? "bg-green-500 text-white self-end"
                                : "bg-gray-700 text-white self-start"
                        }`}>
                            {message.isUser && message.text}
                            {!message.isUser && <Typewriter text={message.text} typeSpeed={1} cursorColor="transparent" />}
                        </div>
                    </div>
                ))}
            </div>
            <div className="p-4 flex">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    placeholder="Message Chatbot..."
                    className="flex-grow p-3 rounded-full bg-gray-800"
                />
                <button
                    onClick={sendMessage}
                    className={`px-4 py-2 rounded-full ${
                        isLoading ? "bg-gray-400 cursor-not-allowed"
                            : "bg-green-500 hover:bg-green-600 text-white"
                    }`}
                >
                    {isLoading ? (
                        <div className="animate-spin rounded-full h-4 w-4 border-t-2"/>
                    ) : "⬆"}
                </button>
            </div>
        </div>
    )
}

export default App
