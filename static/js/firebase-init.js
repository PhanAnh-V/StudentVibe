let firebaseApp;
let firebaseAuth;

fetch('/firebase-config')
    .then(response => response.json())
    .then(config => {
        // Initialize Firebase
        firebaseApp = firebase.initializeApp(config);
        firebaseAuth = firebase.auth();
        console.log("Firebase initialized successfully.");

        // This is a listener that will log user status changes.
        // It's a good way to confirm everything is working later.
        firebaseAuth.onAuthStateChanged(user => {
            if (user) {
                console.log("User is signed in:", user.uid);
            } else {
                console.log("User is signed out.");
            }
        });
    })
    .catch(error => console.error("Error initializing Firebase:", error));