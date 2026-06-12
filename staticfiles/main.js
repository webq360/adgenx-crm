document.addEventListener('DOMContentLoaded', function() {
    const sidebar = document.querySelector('.sidebar');
    const sidebarToggle = document.querySelector('[aria-label="Toggle sidebar"]');

    if (sidebar && sidebarToggle) {
        sidebarToggle.addEventListener('click', function(e) {
            e.stopPropagation();
            sidebar.classList.toggle('show');
        });
    }

    document.addEventListener('click', function(e) {
        if (sidebar.classList.contains('show') && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
            sidebar.classList.remove('show');
        }
    });

    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(function(alert) {
        // Add 'show' class to trigger fade-in
        setTimeout(() => {
            alert.classList.add('show');
        }, 50); // Small delay to ensure the element is rendered before adding the class

        // Set timeout to close the alert
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Calculator logic
    const amountInput = document.getElementById('amountInput');
    const rateInput = document.getElementById('rateInput');
    const resultDisplay = document.getElementById('resultDisplay');

    function calculateResult() {
        const amount = parseFloat(amountInput.value);
        const rate = parseFloat(rateInput.value);

        if (!isNaN(amount) && !isNaN(rate)) {
            const result = amount * rate;
            resultDisplay.textContent = `${result.toFixed(0)}`;
        } else {
            resultDisplay.textContent = '0';
        }
    }

    if (amountInput && rateInput && resultDisplay) {
        amountInput.addEventListener('input', calculateResult);
        rateInput.addEventListener('input', calculateResult);
        calculateResult(); // Initial call
    }
});

const developer_info = () => {
  const info = {
        'name': 'Md Jowel',
        'github': 'https://github.com/mohammad-jowel',
        'linkedin': 'https://www.linkedin.com/in/md-jowel-539775251/'
    };
    console.log(info);
};

function toggleDropdown() {
    document.getElementById("profileDropdown").classList.toggle("show");
}

// Close the dropdown if the user clicks outside of it
window.onclick = function(event) {
    if (!event.target.matches('.avatar') && !event.target.matches('.avatar img')) {
        var dropdowns = document.getElementsByClassName("dropdown-content");
        for (var i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
}