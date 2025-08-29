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
});
