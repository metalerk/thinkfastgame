// Connect to the WebSocket server
const wsProtocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
const ws = new WebSocket(`${wsProtocol}://${window.location.host}/ws/quiz`);

ws.onopen = () => {
    console.log("Connected to the WebSocket server.");
};

ws.onmessage = (event) => {
    const message = event.data;
    const feedback = document.getElementById("feedback");
    const questionBox = document.getElementById("current-question");

    if (message.startsWith("New question:")) {
        const question = message.replace("New question:", "").trim();
        questionBox.textContent = question;
        feedback.textContent = "";
        document.getElementById("answer-input").value = "";
        M.updateTextFields();
    } else if (message.startsWith("Current question:")) {
        const question = message.replace("Current question:", "").trim();
        questionBox.textContent = question;
        feedback.textContent = "";
        document.getElementById("answer-input").value = "";
        M.updateTextFields();
    } else {
        feedback.textContent = message;
    }
};

ws.onclose = () => {
    console.log("Disconnected from the WebSocket server.");
};

document.getElementById("submit-answer").addEventListener("click", () => {
    const answer = document.getElementById("answer-input").value;
    if (answer.trim() !== "") {
        ws.send(answer);
        document.getElementById("answer-input").value = "";
    }
});

// Fetch the initial question on page load
async function fetchInitialQuestion() {
    try {
        const response = await fetch('/current_question');
        const data = await response.json();
        if (data.id !== 0) {
            document.getElementById("current-question").textContent = data.question;
        } else {
            document.getElementById("current-question").textContent = data.question;
        }
    } catch (error) {
        console.error("Error fetching the initial question:", error);
    }
}

fetchInitialQuestion();
