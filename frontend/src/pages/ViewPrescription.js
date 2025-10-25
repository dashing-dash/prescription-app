import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const ViewPrescription = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [prescription, setPrescription] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchPrescription();
  }, [id]);

  const fetchPrescription = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/prescriptions/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPrescription(response.data);
    } catch (error) {
      toast.error("Failed to fetch prescription");
      navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const handleDownloadPDF = async () => {
    try {
      const token = localStorage.getItem('token');
      // Open PDF directly from backend URL
      const pdfUrl = `${API}/prescriptions/${id}/pdf?inline=true`;
      window.open(pdfUrl + `&token=${token}`, '_blank');
      toast.success("Prescription opened in new tab");
    } catch (error) {
      toast.error("Failed to open prescription");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 via-white to-green-50">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (!prescription) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-blue-100 sticky top-0 z-50 shadow-sm">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <Button
              onClick={() => navigate('/')}
              variant="ghost"
              className="text-gray-700 hover:text-gray-900"
              data-testid="back-to-dashboard-button"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Dashboard
            </Button>
            <Button
              onClick={handleDownloadPDF}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg"
              data-testid="download-pdf-view-button"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
              </svg>
              Open PDF
            </Button>
          </div>
        </div>
      </header>

      {/* Prescription Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white/90 backdrop-blur-sm rounded-2xl border border-blue-100 p-12 shadow-2xl" data-testid="prescription-view">
          {/* Doctor Header */}
          <div className="text-center border-b-2 border-blue-200 pb-6 mb-8">
            <h1 className="text-3xl font-bold text-blue-700 mb-1">Dr. Sanjiv Maheshwari</h1>
            <p className="text-gray-600">MBBS, MD (Medicine)</p>
          </div>

          {/* Patient Information */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Prescription</h2>
            <div className="grid grid-cols-2 gap-4 bg-blue-50 p-4 rounded-lg border border-blue-100">
              <div>
                <p className="text-sm text-gray-600 mb-1">Patient Name</p>
                <p className="text-base font-semibold text-gray-900" data-testid="view-patient-name">{prescription.patient_name}</p>
              </div>
              {prescription.patient_age && (
                <div>
                  <p className="text-sm text-gray-600 mb-1">Age</p>
                  <p className="text-base font-semibold text-gray-900" data-testid="view-patient-age">{prescription.patient_age} years</p>
                </div>
              )}
              <div>
                <p className="text-sm text-gray-600 mb-1">Date</p>
                <p className="text-base font-semibold text-gray-900" data-testid="view-prescription-date">{prescription.date}</p>
              </div>
              {prescription.diagnosis && (
                <div className="col-span-2">
                  <p className="text-sm text-gray-600 mb-1">Diagnosis</p>
                  <p className="text-base font-semibold text-gray-900" data-testid="view-diagnosis">{prescription.diagnosis}</p>
                </div>
              )}
            </div>
          </div>

          {/* Medicines */}
          <div className="mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Rx</h2>
            <div className="border border-gray-200 rounded-lg overflow-hidden">
              <table className="w-full" data-testid="medicines-table">
                <thead>
                  <tr className="bg-blue-100 border-b border-gray-200">
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Medicine</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Dosage</th>
                    <th className="px-4 py-3 text-left text-sm font-semibold text-gray-900">Frequency</th>
                  </tr>
                </thead>
                <tbody>
                  {prescription.medicines.map((medicine, index) => (
                    <tr key={index} className="border-b border-gray-100 last:border-b-0 hover:bg-gray-50" data-testid={`medicine-row-${index}`}>
                      <td className="px-4 py-3 text-gray-900">{medicine.name}</td>
                      <td className="px-4 py-3 text-gray-700">{medicine.dosage}</td>
                      <td className="px-4 py-3 text-gray-700">{medicine.frequency}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Notes */}
          {prescription.doctor_notes && (
            <div className="mb-8">
              <h2 className="text-xl font-semibold text-gray-900 mb-3">Notes</h2>
              <p className="text-gray-700 bg-yellow-50 p-4 rounded-lg border border-yellow-200" data-testid="view-doctor-notes">
                {prescription.doctor_notes}
              </p>
            </div>
          )}

          {/* Signature */}
          <div className="mt-12 pt-8 border-t border-gray-200">
            <p className="text-base font-semibold text-gray-900">Dr. Sanjiv Maheshwari</p>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ViewPrescription;