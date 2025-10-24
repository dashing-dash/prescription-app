import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import axios from "axios";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { format } from "date-fns";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

const CreatePrescription = () => {
  const navigate = useNavigate();
  const [formData, setFormData] = useState({
    patient_name: "",
    patient_age: "",
    date: format(new Date(), 'yyyy-MM-dd'),
    doctor_notes: ""
  });
  const [medicines, setMedicines] = useState([{ name: "", dosage: "", frequency: "" }]);
  const [medicineSearch, setMedicineSearch] = useState("");
  const [medicineSuggestions, setMedicineSuggestions] = useState([]);
  const [activeSearchIndex, setActiveSearchIndex] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (medicineSearch && activeSearchIndex !== null) {
      searchMedicines(medicineSearch);
    } else {
      setMedicineSuggestions([]);
    }
  }, [medicineSearch, activeSearchIndex]);

  const searchMedicines = async (query) => {
    try {
      const token = localStorage.getItem('token');
      const response = await axios.get(`${API}/medicines/search?q=${query}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setMedicineSuggestions(response.data);
    } catch (error) {
      console.error("Failed to search medicines", error);
    }
  };

  const handleMedicineInputChange = (index, field, value) => {
    const updatedMedicines = [...medicines];
    updatedMedicines[index][field] = value;
    setMedicines(updatedMedicines);

    if (field === 'name') {
      setActiveSearchIndex(index);
      setMedicineSearch(value);
    }
  };

  const selectMedicine = (index, medicine) => {
    const updatedMedicines = [...medicines];
    updatedMedicines[index].name = medicine.name;
    setMedicines(updatedMedicines);
    setMedicineSuggestions([]);
    setActiveSearchIndex(null);
    setMedicineSearch("");
  };

  const addMedicine = () => {
    setMedicines([...medicines, { name: "", dosage: "", frequency: "" }]);
  };

  const removeMedicine = (index) => {
    if (medicines.length > 1) {
      const updatedMedicines = medicines.filter((_, i) => i !== index);
      setMedicines(updatedMedicines);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!formData.patient_name || medicines.some(m => !m.name || !m.dosage || !m.frequency)) {
      toast.error("Please fill all required fields");
      return;
    }

    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const prescriptionData = {
        ...formData,
        patient_age: formData.patient_age ? parseInt(formData.patient_age) : null,
        medicines: medicines
      };

      const response = await axios.post(`${API}/prescriptions`, prescriptionData, {
        headers: { Authorization: `Bearer ${token}` }
      });

      toast.success("Prescription created successfully!");
      navigate(`/prescription/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || "Failed to create prescription");
    } finally {
      setLoading(false);
    }
  };

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
              data-testid="back-button"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Dashboard
            </Button>
          </div>
        </div>
      </header>

      {/* Form */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-white/80 backdrop-blur-sm rounded-2xl border border-blue-100 p-8 shadow-xl">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">New Prescription</h1>
          <p className="text-gray-600 mb-8">Fill in the patient and medicine details</p>

          <form onSubmit={handleSubmit} className="space-y-8">
            {/* Patient Information */}
            <div className="space-y-4">
              <h2 className="text-xl font-semibold text-gray-900 border-b pb-2">Patient Information</h2>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="patient_name" className="text-gray-700 font-medium">Patient Name *</Label>
                  <Input
                    id="patient_name"
                    type="text"
                    value={formData.patient_name}
                    onChange={(e) => setFormData({ ...formData, patient_name: e.target.value })}
                    placeholder="Enter patient name"
                    className="mt-1.5 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    required
                    data-testid="patient-name-input"
                  />
                </div>

                <div>
                  <Label htmlFor="patient_age" className="text-gray-700 font-medium">Patient Age</Label>
                  <Input
                    id="patient_age"
                    type="number"
                    value={formData.patient_age}
                    onChange={(e) => setFormData({ ...formData, patient_age: e.target.value })}
                    placeholder="Enter age"
                    className="mt-1.5 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                    data-testid="patient-age-input"
                  />
                </div>
              </div>

              <div>
                <Label htmlFor="date" className="text-gray-700 font-medium">Date *</Label>
                <Input
                  id="date"
                  type="date"
                  value={formData.date}
                  onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                  className="mt-1.5 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                  required
                  data-testid="prescription-date-input"
                />
              </div>
            </div>

            {/* Medicines */}
            <div className="space-y-4">
              <div className="flex items-center justify-between border-b pb-2">
                <h2 className="text-xl font-semibold text-gray-900">Medicines</h2>
                <Button
                  type="button"
                  onClick={addMedicine}
                  variant="outline"
                  className="border-blue-200 hover:bg-blue-50 text-blue-600 rounded-lg"
                  data-testid="add-medicine-button"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                  Add Medicine
                </Button>
              </div>

              {medicines.map((medicine, index) => (
                <div key={index} className="p-4 bg-gray-50 rounded-lg border border-gray-200 space-y-3">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium text-gray-700">Medicine {index + 1}</span>
                    {medicines.length > 1 && (
                      <Button
                        type="button"
                        onClick={() => removeMedicine(index)}
                        variant="ghost"
                        size="sm"
                        className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        data-testid={`remove-medicine-button-${index}`}
                      >
                        Remove
                      </Button>
                    )}
                  </div>

                  <div className="relative">
                    <Label className="text-gray-700 font-medium">Medicine Name *</Label>
                    <Input
                      type="text"
                      value={medicine.name}
                      onChange={(e) => handleMedicineInputChange(index, 'name', e.target.value)}
                      placeholder="Search medicine..."
                      className="mt-1.5 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                      required
                      data-testid={`medicine-name-input-${index}`}
                    />
                    {activeSearchIndex === index && medicineSuggestions.length > 0 && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-48 overflow-y-auto" data-testid="medicine-suggestions">
                        {medicineSuggestions.map((med) => (
                          <div
                            key={med.id}
                            onClick={() => selectMedicine(index, med)}
                            className="px-4 py-2 hover:bg-blue-50 cursor-pointer border-b border-gray-100 last:border-b-0"
                            data-testid={`medicine-suggestion-${med.id}`}
                          >
                            <div className="font-medium text-gray-900">{med.name}</div>
                            {med.common_dosages.length > 0 && (
                              <div className="text-xs text-gray-600 mt-1">
                                Common: {med.common_dosages.join(', ')}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <Label className="text-gray-700 font-medium">Dosage *</Label>
                      <Input
                        type="text"
                        value={medicine.dosage}
                        onChange={(e) => handleMedicineInputChange(index, 'dosage', e.target.value)}
                        placeholder="e.g., 500mg"
                        className="mt-1.5 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                        required
                        data-testid={`medicine-dosage-input-${index}`}
                      />
                    </div>

                    <div>
                      <Label className="text-gray-700 font-medium">Frequency *</Label>
                      <Input
                        type="text"
                        value={medicine.frequency}
                        onChange={(e) => handleMedicineInputChange(index, 'frequency', e.target.value)}
                        placeholder="e.g., Twice daily"
                        className="mt-1.5 h-11 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                        required
                        data-testid={`medicine-frequency-input-${index}`}
                      />
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Doctor Notes */}
            <div>
              <Label htmlFor="doctor_notes" className="text-gray-700 font-medium">Doctor's Notes</Label>
              <Textarea
                id="doctor_notes"
                value={formData.doctor_notes}
                onChange={(e) => setFormData({ ...formData, doctor_notes: e.target.value })}
                placeholder="Add any additional notes or instructions..."
                className="mt-1.5 min-h-24 border-gray-200 focus:border-blue-500 focus:ring-blue-500"
                data-testid="doctor-notes-input"
              />
            </div>

            {/* Submit Button */}
            <div className="flex justify-end gap-3 pt-6 border-t">
              <Button
                type="button"
                variant="outline"
                onClick={() => navigate('/')}
                className="border-gray-300 hover:bg-gray-50 rounded-lg px-6"
              >
                Cancel
              </Button>
              <Button
                type="submit"
                className="bg-gradient-to-r from-blue-500 to-blue-600 hover:from-blue-600 hover:to-blue-700 text-white font-medium rounded-lg shadow-md hover:shadow-lg px-8"
                disabled={loading}
                data-testid="submit-prescription-button"
              >
                {loading ? "Creating..." : "Create Prescription"}
              </Button>
            </div>
          </form>
        </div>
      </main>
    </div>
  );
};

export default CreatePrescription;