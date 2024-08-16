const dropArea = document.getElementById("drop-area");
const inputFile = document.getElementById("file-input");
const imageView = document.getElementById("file-view");
const loadingSpinner = document.getElementById("loading-spinner");

// Handle file input change
inputFile.addEventListener("change", uploadImage);

// Handle drag over event
dropArea.addEventListener("dragover", function(e) {
    e.preventDefault();
    dropArea.classList.add("dragover");
});

// Handle drag leave event
dropArea.addEventListener("dragleave", () => {
    dropArea.classList.remove("dragover");
});

// Handle drop event
dropArea.addEventListener("drop", function(e) {
    e.preventDefault();
    dropArea.classList.remove("dragover");
    inputFile.files = e.dataTransfer.files;
    handleFile();
});

// Handle click event to toggle "clicked" class
dropArea.addEventListener("click", () => {
    dropArea.classList.toggle("clicked");
});

function handleFile() {
    const file = inputFile.files[0];
    if (file) {
        const fileType = file.type;

        if (fileType.startsWith('image/')) {
            /* displayImage(file);
            uploadFile(file); */
        } else if (file.name.endsWith('.csv')) {
            displayCSVIcon();
            uploadFile(file, '/upload-csv');
        } else {
            alert('Unsupported file type. Please upload an image or a CSV file.');
        }
    }
}

function displayCSVIcon() {
    imageView.style.backgroundImage = `url('/static/csv-icon.png')`;
    imageView.textContent = "";
    imageView.style.border = 0;
}

function uploadImage() {
    const imgLink = URL.createObjectURL(inputFile.files[0]);
    imageView.style.backgroundImage = `url(${imgLink})`;
    imageView.textContent = "";
    imageView.style.border = 0;
}

function uploadFile(file, endpoint = '/upload') {
    const formData = new FormData();
    formData.append('file', file);

    fetch(endpoint, {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            console.log('File uploaded successfully.');
        } else {
            console.error('Error uploading file:', data.error);
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

document.getElementById('upload-form').addEventListener('submit', function(e) {
    e.preventDefault();
    loadingSpinner.classList.remove("hidden"); // Show spinner

    const formData = new FormData(this);

    fetch('/compare', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        const comparisonText = document.getElementById('comparison-text');
        
        if (data.success) {
            comparisonText.textContent = data.comparison_result;
        } else {
            comparisonText.textContent = 'Error: ' + (data.error || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const comparisonText = document.getElementById('comparison-text');
        comparisonText.textContent = 'Error occurred. Please try again.';
    })
    .finally(() => {
        loadingSpinner.classList.add("hidden"); // Hide spinner
    });
});