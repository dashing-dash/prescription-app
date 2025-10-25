import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const Dashboard = () => {
  const [prescriptions, setPrescriptions] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [prescriptionToDelete, setPrescriptionToDelete] = useState(null);
  const navigate = useNavigate();
  const doctorName = localStorage.getItem('doctorName') || 'Doctor';

  useEffect(() => {
    fetchPrescriptions();
  }, [searchQuery]);

  const fetchPrescriptions = async () => {
    try {
      const token = localStorage.getItem('token');
      const url = searchQuery ? `${API}/prescriptions?patient_name=${searchQuery}` : `${API}/prescriptions`;
      const response = await axios.get(url, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setPrescriptions(response.data);
    } catch (error) {
      toast.error("Failed to fetch prescriptions");
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('doctorName');
    navigate('/login');
  };

  const handleDownloadPDF = async (prescriptionId, e) => {
    e.stopPropagation();
    try {
      const token = localStorage.getItem('token');
      // Open PDF directly from backend URL
      const pdfUrl = `${API}/prescriptions/${prescriptionId}/pdf?inline=true`;
      window.open(pdfUrl + `&token=${token}`, '_blank');
      toast.success("Prescription opened in new tab");
    } catch (error) {
      toast.error("Failed to open prescription");
    }
  };

  const confirmDelete = (prescriptionId, e) => {
    e.stopPropagation();
    setPrescriptionToDelete(prescriptionId);
    setDeleteDialogOpen(true);
  };

  const handleDelete = async () => {
    try {
      const token = localStorage.getItem('token');
      await axios.delete(`${API}/prescriptions/${prescriptionToDelete}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      toast.success("Prescription deleted successfully");
      fetchPrescriptions();
    } catch (error) {
      toast.error("Failed to delete prescription");
    } finally {
      setDeleteDialogOpen(false);
      setPrescriptionToDelete(null);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      {/* Header */}
      <header className="bg-white/80 backdrop-blur-md border-b border-blue-100 sticky top-0 z-50 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center shadow-md">
                <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Prescription Manager</h1>
                <p className="text-sm text-gray-600">{doctorName}</p>
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                onClick={() => navigate('/medicines')}
                variant="outline"
                className="border-gray-300 hover:bg-gray-50 rounded-lg"
                data-testid="medicines-manager-button"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
                </svg>
                Medicines
              </Button>
              <Button
                onClick={() => navigate('/create')}
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg px-6"
                data-testid="create-prescription-button"
              >
                <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                New Prescription
              </Button>
              <Button
                onClick={handleLogout}
                variant="outline"
                className="border-gray-300 hover:bg-gray-50 rounded-lg"
                data-testid="logout-button"
              >
                Logout
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Search Bar */}
        <div className="mb-8">
          <div className="relative max-w-md">
            <svg className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <Input
              type="text"
              placeholder="Search by patient name..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500 rounded-lg bg-white/80 backdrop-blur-sm"
              data-testid="search-patient-input"
            />
          </div>
        </div>

        {/* Prescriptions List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          </div>
        ) : prescriptions.length === 0 ? (
          <div className="text-center py-12 bg-white/60 backdrop-blur-sm rounded-2xl border border-blue-100">
            <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-1">No prescriptions found</h3>
            <p className="text-gray-600 mb-6">Get started by creating your first prescription</p>
            <Button
              onClick={() => navigate('/create')}
              className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white rounded-lg shadow-md"
            >
              Create Prescription
            </Button>
          </div>
        ) : (
          <div className="grid gap-4" data-testid="prescriptions-list">
            {prescriptions.map((prescription) => (
              <div
                key={prescription.id}
                className="bg-white/80 backdrop-blur-sm rounded-xl border border-blue-100 p-6 hover:shadow-lg transition-all cursor-pointer"
                onClick={() => navigate(`/prescription/${prescription.id}`)}
                data-testid={`prescription-card-${prescription.id}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-3">
                      <h3 className="text-lg font-bold text-gray-900">{prescription.patient_name}</h3>
                      {prescription.patient_age && (
                        <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                          {prescription.patient_age} years
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 text-sm text-gray-600 mb-2">
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                      {prescription.date}
                    </div>
                    {prescription.diagnosis && (
                      <div className="mb-3 text-sm">
                        <span className="font-medium text-gray-700">Diagnosis:</span>
                        <span className="text-gray-600 ml-2">{prescription.diagnosis}</span>
                      </div>
                    )}
                    <div className="flex flex-wrap gap-2">
                      {prescription.medicines.map((med, idx) => (
                        <span key={idx} className="px-3 py-1 bg-green-50 text-green-700 rounded-lg text-sm border border-green-200">
                          {med.name}
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      onClick={(e) => handleDownloadPDF(prescription.id, e)}
                      variant="outline"
                      size="sm"
                      className="border-blue-200 hover:bg-blue-50 rounded-lg"
                      data-testid={`download-pdf-button-${prescription.id}`}
                    >
                      <svg className="w-5 h-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                      </svg>
                    </Button>
                    <Button
                      onClick={(e) => confirmDelete(prescription.id, e)}
                      variant="outline"
                      size="sm"
                      className="border-red-200 hover:bg-red-50 rounded-lg"
                      data-testid={`delete-prescription-button-${prescription.id}`}
                    >
                      <svg className="w-5 h-5 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>

      {/* Delete Confirmation Dialog */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Delete Prescription</AlertDialogTitle>
            <AlertDialogDescription>
              Are you sure you want to delete this prescription? This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDelete}
              className="bg-red-600 hover:bg-red-700"
              data-testid="confirm-delete-button"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default Dashboard;