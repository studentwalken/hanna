import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import axios from 'axios';

const SendSMS = () => {
  const { register, handleSubmit, formState: { errors }, reset } = useForm();
  const [mode, setMode] = useState('single'); // single or bulk
  const [phones, setPhones] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [file, setFile] = useState(null);

  useEffect(() => {
    fetchPhones();
  }, []);

  const fetchPhones = async () => {
    try {
      const response = await axios.get('/api/v1/devices');
      setPhones(response.data.items || []);
    } catch (error) {
      console.error('Error fetching phones:', error);
    }
  };

  const onSubmit = async (data) => {
    setIsLoading(true);
    try {
      if (mode === 'single') {
        await axios.post('/api/v1/messages/send', {
          phone_numbers: [data.phone_number],
          content: data.message,
          sender_name: data.sender_name,
          device_id: parseInt(data.device_id),
          sim_slot: data.sim_slot ? parseInt(data.sim_slot) : null,
        });
        toast.success('Message sent successfully!');
      } else {
        // Bulk mode with file upload
        const formData = new FormData();
        formData.append('file', file);
        formData.append('sender_name', data.sender_name);
        formData.append('device_id', parseInt(data.device_id));
        formData.append('sim_slot', data.sim_slot ? parseInt(data.sim_slot) : null);
        formData.append('message_template', data.message);

        await axios.post('/api/v1/messages/bulk-upload', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        toast.success('Bulk messages queued successfully!');
      }
      reset();
      setFile(null);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Failed to send message');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Send SMS</h1>
          <p className="text-gray-600 mt-1">Send messages individually or in bulk</p>
        </div>

        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          {/* Mode Selection */}
          <div className="flex space-x-4 mb-6">
            <button
              onClick={() => setMode('single')}
              className={`px-6 py-3 rounded-lg font-medium transition ${
                mode === 'single'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Single Message
            </button>
            <button
              onClick={() => setMode('bulk')}
              className={`px-6 py-3 rounded-lg font-medium transition ${
                mode === 'bulk'
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Bulk Messages
            </button>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
            {/* Sender Name */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Sender Name
              </label>
              <input
                {...register('sender_name', { required: 'Sender name is required' })}
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="Your name or business name"
              />
              {errors.sender_name && (
                <p className="mt-1 text-sm text-red-600">{errors.sender_name.message}</p>
              )}
            </div>

            {/* Device Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Phone/Device
              </label>
              <select
                {...register('device_id', { required: 'Please select a device' })}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Choose a device...</option>
                {phones.map((phone) => (
                  <option key={phone.id} value={phone.id}>
                    {phone.device_name || 'Unnamed'} - {phone.phone_number || 'No number'} ({phone.status})
                  </option>
                ))}
              </select>
              {errors.device_id && (
                <p className="mt-1 text-sm text-red-600">{errors.device_id.message}</p>
              )}
            </div>

            {/* SIM Slot Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SIM Slot (Optional)
              </label>
              <select
                {...register('sim_slot')}
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <option value="">Auto</option>
                <option value="1">SIM 1</option>
                <option value="2">SIM 2</option>
              </select>
            </div>

            {mode === 'single' ? (
              <>
                {/* Recipient Number */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Recipient Phone Number
                  </label>
                  <input
                    {...register('phone_number', { 
                      required: 'Phone number is required',
                      pattern: {
                        value: /^\+?[\d\s-()]+$/,
                        message: 'Invalid phone number format'
                      }
                    })}
                    type="tel"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="+1234567890"
                  />
                  {errors.phone_number && (
                    <p className="mt-1 text-sm text-red-600">{errors.phone_number.message}</p>
                  )}
                </div>

                {/* Message Content */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message
                  </label>
                  <textarea
                    {...register('message', { 
                      required: 'Message is required',
                      maxLength: {
                        value: 1600,
                        message: 'Message cannot exceed 1600 characters'
                      }
                    })}
                    rows="6"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Type your message here..."
                  />
                  {errors.message && (
                    <p className="mt-1 text-sm text-red-600">{errors.message.message}</p>
                  )}
                  <p className="mt-1 text-sm text-gray-500">
                    Standard SMS: 160 characters | Concatenated SMS: up to 1600 characters
                  </p>
                </div>
              </>
            ) : (
              <>
                {/* File Upload for Bulk */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Upload CSV/Excel File
                  </label>
                  <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
                    <input
                      type="file"
                      accept=".csv,.xlsx,.xls"
                      onChange={(e) => setFile(e.target.files[0])}
                      className="hidden"
                      id="file-upload"
                    />
                    <label htmlFor="file-upload" className="cursor-pointer">
                      <svg className="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48">
                        <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
                      </svg>
                      <p className="mt-2 text-sm text-gray-600">
                        {file ? file.name : 'Click to upload or drag and drop'}
                      </p>
                      <p className="mt-1 text-xs text-gray-500">CSV or Excel (XLSX, XLS)</p>
                    </label>
                  </div>
                  {file && (
                    <p className="mt-2 text-sm text-green-600">File selected: {file.name}</p>
                  )}
                </div>

                {/* Message Template */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Message Template
                  </label>
                  <textarea
                    {...register('message', { 
                      required: 'Message template is required',
                      maxLength: {
                        value: 1600,
                        message: 'Message cannot exceed 1600 characters'
                      }
                    })}
                    rows="6"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                    placeholder="Hello {name}, your message here..."
                  />
                  {errors.message && (
                    <p className="mt-1 text-sm text-red-600">{errors.message.message}</p>
                  )}
                  <p className="mt-1 text-sm text-gray-500">
                    Use {'{name}'} as placeholder for recipient names from your file
                  </p>
                </div>
              </>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isLoading}
              className="w-full py-4 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
            >
              {isLoading ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Sending...
                </span>
              ) : (
                `Send ${mode === 'bulk' ? 'Bulk Messages' : 'Message'}`
              )}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default SendSMS;
