'use client';

import { useState, FormEvent } from 'react';
import { useRouter } from 'next/navigation'; // Import useRouter for redirection
import Link from 'next/link'; // Import Link for Back button

export default function NewClientPage() {
  const router = useRouter(); // Initialize router
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    phone: '',
    incidentDate: '',
    location: '',
    injuryDetails: '',
    medicalExpenses: '', // Store as string initially for input control
    insuranceCompany: '',
    lawyerNotes: '',
    caseType: '', // Default to empty, first option will be selected visually
    verbalQuality: '', // Default to empty
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prevData) => ({
      ...prevData,
      [name]: value,
    }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    setSuccess(null);

    // Basic Validation
    if (!formData.name || !formData.email || !formData.caseType || !formData.verbalQuality) {
      setError('Client Name, Email, Case Type, and Verbal Quality are required.');
      setIsLoading(false);
      return;
    }

    // Prepare data for API (convert medicalExpenses to number)
    const payload = {
        ...formData,
        medicalExpenses: formData.medicalExpenses ? parseFloat(formData.medicalExpenses) : null,
        // Ensure date is handled correctly if needed by backend (e.g., new Date(formData.incidentDate))
        // For now, sending as string as received from date input
    };

    try {
      const response = await fetch('/api/clients', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      // Parse the response as text first
      const responseText = await response.text();
      
      // Try to parse as JSON if possible
      let errorData;
      try {
        errorData = responseText ? JSON.parse(responseText) : {};
      } catch (e) {
        // If JSON parsing fails, use the raw text
        errorData = { message: responseText };
      }

      if (!response.ok) {
        // Handle different types of error responses
        const errorMessage = 
          errorData.error || 
          errorData.message || 
          errorData.details || 
          `HTTP error! status: ${response.status}`;
          
        throw new Error(typeof errorMessage === 'string' ? errorMessage : JSON.stringify(errorMessage));
      }

      // Handle success - we've already parsed the response text
      const result = responseText ? JSON.parse(responseText) : {};
      setSuccess('Client added successfully! Redirecting to dashboard...');
      console.log('Client created:', result);

      // Redirect to dashboard after a short delay
      setTimeout(() => {
        router.push('/dashboard');
      }, 2000);

    } catch (error: unknown) {
      console.error("Failed to create client:", error);
      setError(error instanceof Error ? error.message : "An unknown error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-8 max-w-2xl">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-semibold">Add New Client</h1>
        <Link 
          href="/dashboard" 
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 font-semibold py-2 px-4 rounded inline-flex items-center transition duration-150 ease-in-out"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
          </svg>
          Back to Dashboard
        </Link>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Error: </strong>
          <span className="block sm:inline">{error}</span>
        </div>
      )}
      {success && (
        <div className="bg-green-100 border border-green-400 text-green-700 px-4 py-3 rounded relative mb-4" role="alert">
          <strong className="font-bold">Success: </strong>
          <span className="block sm:inline">{success}</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="bg-white shadow-md rounded px-8 pt-6 pb-8 mb-4">
        {/* Client Info */}
        <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="name">
              Client Name <span className="text-red-500">*</span>
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="name"
              name="name"
              type="text"
              placeholder="John Doe"
              value={formData.name}
              onChange={handleChange}
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="email">
              Email Address <span className="text-red-500">*</span>
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="email"
              name="email"
              type="email"
              placeholder="client@example.com"
              value={formData.email}
              onChange={handleChange}
              required
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="phone">
              Phone Number
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="phone"
              name="phone"
              type="tel"
              placeholder="(555) 123-4567"
              value={formData.phone}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Case Details */}
        <h2 className="text-xl font-semibold mb-4 border-t pt-4 mt-6">Case Details</h2>
        <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="caseType">
              Case Type <span className="text-red-500">*</span>
            </label>
            <select
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-white"
              id="caseType"
              name="caseType"
              value={formData.caseType}
              onChange={handleChange}
              required
            >
              <option value="" disabled>Select Case Type</option>
              <option value="MVA">Motor Vehicle Accident (MVA)</option>
              <option value="Fall">Fall Incident</option>
              <option value="Product Liability">Product Liability</option>
              <option value="Other">Other</option>
            </select>
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="verbalQuality">
              Verbal Quality <span className="text-red-500">*</span>
            </label>
            <select
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline bg-white"
              id="verbalQuality"
              name="verbalQuality"
              value={formData.verbalQuality}
              onChange={handleChange}
              required
            >
              <option value="" disabled>Select Verbal Quality</option>
              <option value="Good">Good Verbal</option>
              <option value="Bad">Bad Verbal</option>
              <option value="Zero">Zero Verbal</option>
              <option value="N/A">N/A</option>
            </select>
          </div>
        </div>

        {/* Incident Details */}
        <h2 className="text-xl font-semibold mb-4 border-t pt-4 mt-6">Incident Details</h2>
        <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="incidentDate">
              Incident Date
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="incidentDate"
              name="incidentDate"
              type="date"
              value={formData.incidentDate}
              onChange={handleChange}
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="location">
              Incident Location
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="location"
              name="location"
              type="text"
              placeholder="123 Main St, Anytown"
              value={formData.location}
              onChange={handleChange}
            />
          </div>
        </div>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="injuryDetails">
            Injury Details
          </label>
          <textarea
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-24"
            id="injuryDetails"
            name="injuryDetails"
            placeholder="Describe the injuries sustained..."
            value={formData.injuryDetails}
            onChange={handleChange}
          />
        </div>

        {/* Financial & Insurance */}
        <h2 className="text-xl font-semibold mb-4 border-t pt-4 mt-6">Financial & Insurance</h2>
        <div className="mb-4 grid grid-cols-1 md:grid-cols-2 gap-4">
           <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="medicalExpenses">
              Medical Expenses ($)
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="medicalExpenses"
              name="medicalExpenses"
              type="number"
              step="0.01" // Allow cents
              placeholder="5000.00"
              value={formData.medicalExpenses}
              onChange={handleChange}
            />
          </div>
          <div>
            <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="insuranceCompany">
              Insurance Company
            </label>
            <input
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              id="insuranceCompany"
              name="insuranceCompany"
              type="text"
              placeholder="Example Insurance Co."
              value={formData.insuranceCompany}
              onChange={handleChange}
            />
          </div>
        </div>

        {/* Notes */}
        <h2 className="text-xl font-semibold mb-4 border-t pt-4 mt-6">Notes</h2>
        <div className="mb-6">
          <label className="block text-gray-700 text-sm font-bold mb-2" htmlFor="lawyerNotes">
            Lawyer Notes (Optional)
          </label>
          <textarea
            className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline h-32"
            id="lawyerNotes"
            name="lawyerNotes"
            placeholder="Internal notes about the case or client..."
            value={formData.lawyerNotes}
            onChange={handleChange}
          />
        </div>

        {/* Submit Button */}
        <div className="flex items-center justify-between border-t pt-6">
          <button
            className="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline disabled:opacity-50 disabled:cursor-not-allowed"
            type="submit"
            disabled={isLoading}
          >
            {isLoading ? 'Submitting...' : 'Add Client'}
          </button>
        </div>
      </form>
    </div>
  );
} 