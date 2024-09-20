chrome.runtime.onMessage.addListener(function(message) {
  if (message.url) {
    fetch("http://127.0.0.1:5000/run-script", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ url: message.url }),
    })
      .then((response) => response.json())
      .then((data) => {
          chrome.runtime.sendMessage({ success: true });
          console.log(data);
      })
      .catch((error) => {
        console.error("Error:", error);
        chrome.runtime.sendMessage({ error: "An error occurred while loading the reviews." });
      });
  }
});
