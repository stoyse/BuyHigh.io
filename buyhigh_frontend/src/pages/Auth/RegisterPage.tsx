import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { registerUser } from '../../apiService'; // Korrigierter Importpfad
import BaseLayout from '../../components/Layout/BaseLayout'; // Pfad anpassen

const RegisterPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [username, setUsername] = useState(''); // Optional
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);

    if (password.length < 6) {
      setError('Password must be at least 6 characters long.');
      setIsLoading(false);
      return;
    }

    try {
      const data = await registerUser({ email, password, username });
      if (data.success) {
        // Optional: Speichere Token oder Benutzerinfos im LocalStorage/Context
        // z.B. localStorage.setItem('token', data.id_token);
        // localStorage.setItem('userId', data.id); // oder data.firebase_uid
        navigate('/login'); // Oder direkt zum Dashboard, falls Registrierung automatisch einloggt
      } else {
        setError(data.message || 'Registration failed. Please try again.');
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    }
    setIsLoading(false);
  };

  return (
    <BaseLayout title="Register - BuyHigh.io">
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background-light via-background-light to-background-accent-light dark:from-background-dark dark:via-background-dark dark:to-background-accent-dark py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8 glass-card shadow-neo-lg border border-gray-200/10 dark:border-gray-700/20 rounded-2xl p-8 md:p-10">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold gradient-text">
              Create your Account
            </h2>
          </div>
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            {error && (
              <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
                <strong className="font-bold">Error: </strong>
                <span className="block sm:inline">{error}</span>
              </div>
            )}
            <div className="rounded-md shadow-sm -space-y-px">
              <div>
                <label htmlFor="username" className="sr-only">
                  Username (Optional)
                </label>
                <input
                  id="username"
                  name="username"
                  type="text"
                  autoComplete="username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white/5 dark:bg-gray-800/40 rounded-t-md focus:outline-none focus:ring-neo-amber focus:border-neo-amber focus:z-10 sm:text-sm"
                  placeholder="Username (Optional)"
                />
              </div>
              <div>
                <label htmlFor="email-address" className="sr-only">
                  Email address
                </label>
                <input
                  id="email-address"
                  name="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white/5 dark:bg-gray-800/40 focus:outline-none focus:ring-neo-amber focus:border-neo-amber focus:z-10 sm:text-sm"
                  placeholder="Email address"
                />
              </div>
              <div>
                <label htmlFor="password" className="sr-only">
                  Password
                </label>
                <input
                  id="password"
                  name="password"
                  type="password"
                  autoComplete="new-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="appearance-none rounded-none relative block w-full px-3 py-3 border border-gray-300 dark:border-gray-600 placeholder-gray-500 dark:placeholder-gray-400 text-gray-900 dark:text-white bg-white/5 dark:bg-gray-800/40 rounded-b-md focus:outline-none focus:ring-neo-amber focus:border-neo-amber focus:z-10 sm:text-sm"
                  placeholder="Password (min. 6 characters)"
                />
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={isLoading}
                className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-neo-amber hover:bg-neo-amber-dark focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-neo-amber-dark disabled:opacity-50 transition-colors duration-150 ease-in-out"
              >
                {isLoading ? (
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                ) : (
                  'Create Account'
                )}
              </button>
            </div>
          </form>
          <div className="text-sm text-center">
            <p className="text-gray-600 dark:text-gray-400">
              Already have an account?
              <button onClick={() => navigate('/login')} className="font-medium text-neo-amber hover:text-neo-amber-dark ml-1">
                Sign in
              </button>
            </p>
          </div>
        </div>
      </div>
    </BaseLayout>
  );
};

export default RegisterPage;
