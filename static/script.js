const dropArea = document.getElementById("drop-area");
const inputFile = document.getElementById("file1");
const imageView = document.getElementById("img-view");
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
    uploadImage();
});

// Handle click event to toggle "clicked" class
dropArea.addEventListener("click", () => {
    dropArea.classList.toggle("clicked");
});

function uploadImage() {
    const imgLink = URL.createObjectURL(inputFile.files[0]);
    imageView.style.backgroundImage = `url(${imgLink})`;
    imageView.textContent = "";
    imageView.style.border = 0;
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