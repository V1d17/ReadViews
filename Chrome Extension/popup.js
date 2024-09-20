document.addEventListener('DOMContentLoaded', function() {
  const chatBox = document.getElementById('chat-box');
  const chatInput = document.getElementById('chat-input');
  const sendButton = document.getElementById('send-button');
  const restaurantNameElement = document.getElementById('restaurant-name');
  const errorOverlay = document.getElementById('error-overlay');
  const loadingOverlay = document.getElementById('loading-overlay'); // Correct ID for loading overlay

  let placeName = ''; // Variable to store the place name

  (async () => {
    const [tab] = await chrome.tabs.query({ active: true, lastFocusedWindow: true });
    chrome.runtime.sendMessage({ popupOpen: true, url: tab.url });
    placeName = await getRestaurantNameFromURL(tab.url);

    restaurantNameElement.textContent = placeName + ' Ai';
  })();

  async function getRestaurantNameFromURL(url) {
    const match = url.match(/\/maps\/place\/([^/]+)/);
    if (match) {
      return match[1].replace(/\+/g, ' ');
    } else {
      return 'Amazing Place'; // or handle the case where there's no match
    }
  }

  function appendMessage(message, fromUser = true) {
    const messageElement = document.createElement('div');
    messageElement.className = `message ${fromUser ? 'user' : 'bot'}`;

    const avatar = document.createElement('img');
    avatar.src = fromUser ? 'images/user.png' : 'images/bot.png';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    messageContent.textContent = message;

    messageElement.appendChild(avatar);
    messageElement.appendChild(messageContent);
    chatBox.appendChild(messageElement);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  async function sendMessageToServer(message) {
    try {
      const response = await fetch('http://127.0.0.1:5000/chat', { // Adjust URL if needed
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        body: JSON.stringify({ 
          query: message,
          place_name: placeName // Add place_name to the request body
        }),
      });

      if (response.ok) {
        const data = await response.json();
        console.log(data);
        return data;
      } else {
        console.error('Server responded with an error');
        return 'Sorry, there was an error processing your request.';
      }
    } catch (error) {
      console.error('Network error:', error);
      return 'Sorry, there was an error processing your request.';
    }
  }

  sendButton.addEventListener('click', async function() {
    const message = chatInput.value.trim();
    if (message) {
      appendMessage(message);
      chatInput.value = '';

      loadingOverlay.style.display = 'flex'; // Show loading overlay when sending message

      // Send the message to the server and get the response
      const botResponse = await sendMessageToServer(message);
      appendMessage(botResponse, false); // Append bot response

      loadingOverlay.style.display = 'none'; // Hide loading overlay after receiving response
    }
  });

  chatInput.addEventListener('keydown', function(event) {
    if (event.key === 'Enter') {
      sendButton.click();
    }
  });

  // Listen for messages from background.js
  chrome.runtime.onMessage.addListener(function(message) {
    if (message.error) {
      errorOverlay.textContent = message.error;
      errorOverlay.style.display = 'flex';
      loadingOverlay.style.display = 'none'; // Hide loading overlay on error
    } else if (message.success) {
      loadingOverlay.style.display = 'none'; // Hide loading overlay on success
    }
  });

  // Show loading overlay initially
  loadingOverlay.style.display = 'flex';
});
