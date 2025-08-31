document.addEventListener('DOMContentLoaded', function() {
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
            const result = amount / rate;
            resultDisplay.textContent = `${result.toFixed(2)}`;
        } else {
            resultDisplay.textContent = '0.00'; // Set to 0.00 if inputs are invalid
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