document.addEventListener('DOMContentLoaded', () => {
    // Get all the necessary DOM elements
    const summarizeForm = document.getElementById('summarize-form');
    const urlInput = document.getElementById('url-input');
    const submitButton = document.getElementById('submit-button');
    const resultContainer = document.getElementById('result-container');
    const loader = document.getElementById('loader');
    const errorMessage = document.getElementById('error-message');
    const summaryOutput = document.getElementById('summary-output');
    const sourcesContainer = document.getElementById('sources-container');
    const sourcesList = document.getElementById('sources-list');

    const apiKey = ""; // API key is handled by the environment

    // Listen for the form submission
    summarizeForm.addEventListener('submit', (e) => {
        e.preventDefault(); // Prevent the form from actually submitting
        const url = urlInput.value.trim();

        // Simple validation
        if (!isValidUrl(url)) {
            displayError("Please enter a valid URL, starting with http:// or https://");
            return;
        }

        // Start the process
        handleSummaryRequest(url);
    });

    /**
     * Handles the summary request process
     */
    async function handleSummaryRequest(url) {
        // 1. Reset UI
        setLoading(true);
        clearResults();

        try {
            // 2. Define the system prompt and user query
            const systemPrompt = "You are an expert summarizer. Your job is to provide a concise, easy-to-read summary of the provided web page content. Respond with the summary in a few bullet points, using markdown for the bullets.";
            const userQuery = `Please summarize the content of this URL: ${url}`;

            // 3. Call the API with exponential backoff
            const result = await fetchWithBackoff(systemPrompt, userQuery);

            // 4. Display the results
            if (result && result.text) {
                displaySummary(result.text, result.sources);
            } else {
                displayError("Could not get a summary from the AI. The response was empty.");
            }
        } catch (error) {
            console.error("Error during summary request:", error);
            displayError(`An error occurred: ${error.message}. Check the console for details.`);
        } finally {
            // 5. Stop loading state
            setLoading(false);
        }
    }

    /**
     * Fetches data from the Gemini API with exponential backoff.
     * This function is required by the instructions for API calls.
     */
    async function fetchWithBackoff(systemPrompt, userQuery, retries = 3, delay = 1000) {
        const apiUrl = `https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key=${apiKey}`;

        // Construct the payload
        const payload = {
            contents: [{ parts: [{ text: userQuery }] }],
            // Use Google Search grounding to allow the model to access the URL
            tools: [{ "google_search": {} }], 
            systemInstruction: {
                parts: [{ text: systemPrompt }]
            },
        };

        for (let i = 0; i < retries; i++) {
            try {
                const response = await fetch(apiUrl, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });

                if (!response.ok) {
                    throw new Error(`API Error: ${response.status} ${response.statusText}`);
                }

                const result = await response.json();
                const candidate = result.candidates?.[0];

                if (candidate && candidate.content?.parts?.[0]?.text) {
                    const text = candidate.content.parts[0].text;
                    
                    // Extract grounding sources
                    let sources = [];
                    const groundingMetadata = candidate.groundingMetadata;
                    if (groundingMetadata && groundingMetadata.groundingAttributions) {
                        sources = groundingMetadata.groundingAttributions
                            .map(attribution => ({
                                uri: attribution.web?.uri,
                                title: attribution.web?.title,
                            }))
                            .filter(source => source.uri && source.title); // Ensure sources are valid
                    }
                    
                    return { text, sources };
                } else {
                    throw new Error("Invalid response structure from API.");
                }
            } catch (error) {
                if (i === retries - 1) {
                    // If this was the last retry, re-throw the error
                    throw error;
                }
                // Wait for the delay and then double it for the next retry
                await new Promise(resolve => setTimeout(resolve, delay));
                delay *= 2;
            }
        }
    }

    /**
     * Displays the summary and sources
     */
    function displaySummary(summaryText, sources) {
        // Convert markdown bullets (* text) to HTML list items
        const htmlSummary = summaryText
            .split('\n')
            .map(line => line.trim())
            .filter(line => line.startsWith('*') || line.startsWith('-'))
            .map(line => `<li>${line.substring(1).trim()}</li>`)
            .join('');

        summaryOutput.innerHTML = `<ul>${htmlSummary || '<p>' + summaryText + '</p>'}</ul>`;

        // Display sources
        if (sources && sources.length > 0) {
            sourcesList.innerHTML = sources
                .map(source => `<li><a href="${source.uri}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:underline">${source.title}</a></li>`)
                .join('');
            sourcesContainer.classList.remove('hidden');
        }
    }

    /**
     * Displays an error message
     */
    function displayError(message) {
        errorMessage.textContent = message;
        errorMessage.classList.remove('hidden');
    }

    /**
     * Clears all previous results and errors
     */
    function clearResults() {
        resultContainer.classList.add('hidden');
        errorMessage.classList.add('hidden');
        summaryOutput.innerHTML = '';
        sourcesList.innerHTML = '';
        sourcesContainer.classList.add('hidden');
    }

    /**
     * Sets the loading state of the UI
     */
    function setLoading(isLoading) {
        if (isLoading) {
            submitButton.disabled = true;
            submitButton.textContent = 'Summarizing...';
            resultContainer.classList.remove('hidden');
            loader.classList.remove('hidden');
        } else {
            submitButton.disabled = false;
            submitButton.textContent = 'Summarize';
            loader.classList.add('hidden');
        }
    }

    /**
     * Simple URL validation
     */
    function isValidUrl(string) {
        try {
            new URL(string);
            return true;
        } catch (_) {
            return false;
        }
    }
});