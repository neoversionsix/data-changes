document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    const formData = new FormData(this);

    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';
    document.getElementById('error').style.display = 'none';

    axios.post('/process', formData, { timeout: 300000 }) // 5-minute timeout
        .then(function (response) {
            document.getElementById('loading').style.display = 'none';
            if (response.data.error) {
                document.getElementById('error').textContent = response.data.error;
                document.getElementById('error').style.display = 'block';
            } else {
                document.getElementById('results').style.display = 'block';
                document.getElementById('new-rows-count').textContent = response.data.new_rows_count;
                document.getElementById('non-existing-rows-count').textContent = response.data.non_existing_rows_count;
                document.getElementById('download-new-rows').disabled = false;
                document.getElementById('download-non-existing-rows').disabled = false;
            }
        })
        .catch(function (error) {
            document.getElementById('loading').style.display = 'none';
            console.error('Error:', error);
            document.getElementById('error').textContent = 'An error occurred while processing the files. Please check the console for more details.';
            document.getElementById('error').style.display = 'block';
        });
});

function downloadFile(downloadType) {
    const formData = new FormData(document.getElementById('upload-form'));
    formData.append('download_type', downloadType);

    document.getElementById('loading').style.display = 'block';
    document.getElementById('error').style.display = 'none';

    axios.post('/download', formData, { responseType: 'blob', timeout: 300000 }) // 5-minute timeout
        .then(function (response) {
            document.getElementById('loading').style.display = 'none';
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', downloadType === 'new_rows' ? 'new_rows.xlsx' : 'non_existing_rows.xlsx');
            document.body.appendChild(link);
            link.click();
            link.remove();
        })
        .catch(function (error) {
            document.getElementById('loading').style.display = 'none';
            console.error('Error:', error);
            document.getElementById('error').textContent = 'An error occurred while downloading the file. Please check the console for more details.';
            document.getElementById('error').style.display = 'block';
        });
}

document.getElementById('download-new-rows').addEventListener('click', function() {
    downloadFile('new_rows');
});

document.getElementById('download-non-existing-rows').addEventListener('click', function() {
    downloadFile('non_existing_rows');
});