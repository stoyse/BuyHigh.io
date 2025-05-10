async function initializeFirebase() {
  try {
    const response = await fetch('/auth/firebase-config');
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `Failed to fetch Firebase config: ${response.statusText}`);
    }
    const firebaseConfig = await response.json();

    if (!firebaseConfig.apiKey || !firebaseConfig.authDomain || !firebaseConfig.projectId) {
        console.error('Firebase config from server is incomplete:', firebaseConfig);
        alert('Firebase configuration is incomplete. Please contact support.');
        return null;
    }

    // Firebase initialisieren
    firebase.initializeApp(firebaseConfig);
    return firebase.auth();
  } catch (error) {
    console.error("Error initializing Firebase:", error);
    alert(`Could not initialize Firebase: ${error.message}`);
    return null;
  }
}

document.addEventListener('DOMContentLoaded', async () => {
  const auth = await initializeFirebase();

  if (!auth) {
    console.error("Firebase Auth SDK not initialized. Google Sign-In button will not work.");
    return;
  }

  const googleSignInButton = document.getElementById('google-signin-btn');

  if (googleSignInButton) {
    googleSignInButton.addEventListener('click', () => {
      const provider = new firebase.auth.GoogleAuthProvider();
      auth.signInWithPopup(provider)
        .then((result) => {
          const user = result.user;
          user.getIdToken().then((idToken) => {
            fetch('/auth/google-signin', { // Stellen Sie sicher, dass dieser Endpunkt in Ihrem Backend existiert
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ idToken: idToken }),
            })
            .then(response => response.json())
            .then(data => {
              if (data.success) {
                window.location.href = data.redirect_url || '/';
              } else {
                alert('Google Sign-In failed on server: ' + (data.error || 'Unknown error'));
              }
            })
            .catch((error) => {
              console.error('Error sending ID token to backend:', error);
              alert('Error communicating with the server during Google Sign-In.');
            });
          });
        })
        .catch((error) => {
          console.error("Google Sign-In Popup Error:", error.code, error.message);
          alert("Google Sign-In Error: " + error.message);
        });
    });
  }
});
