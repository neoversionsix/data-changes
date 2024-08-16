document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    axios.post('/process', formData)
        .then(function (response) {
            document.getElementById('loading').style.display = 'none';
            if (response.data.error) {
                document.getElementById('error').textContent = response.data.error;
                document.getElementById('error').style.display = 'block';
                console.error('Server returned an error:', response.data.error);
            } else {
                document.getElementById('results').style.display = 'block';
                document.getElementById('new-rows-count').textContent = response.data.new_rows_count;
                document.getElementById('non-existing-rows-count').textContent = response.data.non_existing_rows_count;
                document.getElementById('download-new-rows').disabled = false;
                document.getElementById('download-non-existing-rows').disabled = false;
            }
            fetchLogs();
        })
        .catch(function (error) {
            document.getElementById('loading').style.display = 'none';
            console.error('Axios error:', error);
            if (error.response) {
                console.error('Error data:', error.response.data);
                console.error('Error status:', error.response.status);
                console.error('Error headers:', error.response.headers);
            } else if (error.request) {
                console.error('Error request:', error.request);
            } else {
                console.error('Error message:', error.message);
            }
            document.getElementById('error').textContent = 'An error occurred while processing the files. Please check the browser console for more details.';
            document.getElementById('error').style.display = 'block';
            fetchLogs();
        });
});

// ... (rest of the code remains the same)