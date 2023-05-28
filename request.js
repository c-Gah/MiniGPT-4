async function sendImage() {
    // Fetch the Google logo
    const imageResponse = await fetch("https://upload.wikimedia.org/wikipedia/commons/thumb/4/41/Sunflower_from_Silesia2.jpg/1200px-Sunflower_from_Silesia2.jpg");
    const blob = await imageResponse.blob();

    // Create a new FormData instance
    const formData = new FormData();
    formData.append("file", blob, "google_logo.png");
    formData.append("question", "What is the image about");

    // Send the image and question to the server
    const response = await fetch("http://81.166.173.12:10156/upload_ask_answer", {
        method: 'POST',
        body: formData,
    });

    // Check if the request was successful
    if (!response.ok) {
        console.error("An error occurred", response);
        return;
    }

    // Log the response from the server
    const data = await response.json();
    console.log(data.answer);
}

function sendImagesRepeatedly() {
    let i = 0;
    const intervalId = setInterval(() => {
        if (i >= 10) {
            clearInterval(intervalId); // stop when 100 requests have been sent
        } else {
            sendImage();
            console.log("sent request")
            i++;
        }
    }, 1000);
}

// Call the function
sendImagesRepeatedly();
