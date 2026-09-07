import React, { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import axios from 'axios';

const APIKeys = () => {
  const { register, handleSubmit, reset } = useForm();
  const [apiKeys, setApiKeys] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchApiKeys();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const response = await axios.get('/api/v1/api-keys');
      setApiKeys(response.data.items || []);
    } catch (error) {
      console.error('Error fetching API keys:', error);
    } finally {
      setLoading(false);
    }
  };

  const onSubmit = async (data) => {
    try {
      await axios.post('/api/v1/api-keys', {
        name: data.name,
        rate_limit: parseInt(data.rate_limit) || 100,
      });
      toast.success('API key created successfully!');
      reset();
      fetchApiKeys();
    } catch (error) {
      toast.error('Failed to create API key');
    }
  };

  const toggleKeyStatus = async (keyId, currentStatus) => {
    try {
      await axios.patch(`/api/v1/api-keys/${keyId}`, {
        is_active: !currentStatus
      });
      toast.success('API key status updated');
      fetchApiKeys();
    } catch (error) {
      toast.error('Failed to update API key');
    }
  };

  const deleteKey = async (keyId) => {
    if (!confirm('Are you sure you want to delete this API key?')) return;
    
    try {
      await axios.delete(`/api/v1/api-keys/${keyId}`);
      toast.success('API key deleted');
      fetchApiKeys();
    } catch (error) {
      toast.error('Failed to delete API key');
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    toast.success('Copied to clipboard!');
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">API Keys</h1>
          <p className="text-gray-600 mt-1">Manage API keys for external applications</p>
        </div>

        {/* Create New Key */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6 mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Create New API Key</h2>
          <form onSubmit={handleSubmit(onSubmit)} className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Key Name</label>
              <input
                {...register('name', { required: 'Name is required' })}
                type="text"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="My Application"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Rate Limit (per hour)</label>
              <input
                {...register('rate_limit')}
                type="number"
                className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                placeholder="100"
              />
            </div>
            <div className="flex items-end">
              <button
                type="submit"
                className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 transition"
              >
                Generate Key
              </button>
            </div>
          </form>
        </div>

        {/* API Keys List */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="px-6 py-4 border-b border-gray-200">
            <h2 className="text-lg font-semibold text-gray-900">Your API Keys</h2>
          </div>
          
          {apiKeys.length > 0 ? (
            <div className="divide-y divide-gray-200">
              {apiKeys.map((key) => (
                <div key={key.id} className="p-6 hover:bg-gray-50">
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center space-x-3">
                        <h3 className="font-semibold text-gray-900">{key.name}</h3>
                        <span className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                          key.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                        }`}>
                          {key.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                      <div className="mt-2 flex items-center space-x-3">
                        <code className="px-3 py-1 bg-gray-100 rounded text-sm font-mono">
                          {key.key_prefix}••••••••••••••••
                        </code>
                        <button
                          onClick={() => copyToClipboard(key.key)}
                          className="text-sm text-indigo-600 hover:text-indigo-900"
                        >
                          Show Full Key
                        </button>
                      </div>
                      <p className="mt-2 text-sm text-gray-500">
                        Rate Limit: {key.rate_limit || 'Unlimited'} requests/hour • 
                        Created: {new Date(key.created_at).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={() => toggleKeyStatus(key.id, key.is_active)}
                        className={`px-4 py-2 text-sm font-medium rounded-lg transition ${
                          key.is_active
                            ? 'bg-yellow-100 text-yellow-800 hover:bg-yellow-200'
                            : 'bg-green-100 text-green-800 hover:bg-green-200'
                        }`}
                      >
                        {key.is_active ? 'Deactivate' : 'Activate'}
                      </button>
                      <button
                        onClick={() => deleteKey(key.id)}
                        className="px-4 py-2 text-sm font-medium text-red-600 bg-red-50 rounded-lg hover:bg-red-100 transition"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="p-12 text-center">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No API keys</h3>
              <p className="mt-1 text-sm text-gray-500">Create your first API key above</p>
            </div>
          )}
        </div>

        {/* API Documentation */}
        <div className="mt-8 bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">API Documentation</h2>
          <div className="prose prose-sm max-w-none">
            <h3>Base URL</h3>
            <code className="block bg-gray-100 p-3 rounded-lg mt-2">https://your-domain.com/api/v1/external</code>
            
            <h3 className="mt-6">Authentication</h3>
            <p>Include your API key in the Authorization header:</p>
            <code className="block bg-gray-100 p-3 rounded-lg mt-2">Authorization: Bearer YOUR_API_KEY</code>
            
            <h3 className="mt-6">Send SMS Endpoint</h3>
            <div className="bg-gray-100 p-4 rounded-lg mt-2">
              <p className="font-mono text-sm">POST /api/v1/external/send</p>
              <pre className="mt-2 text-sm overflow-x-auto">
{`{
  "sender_name": "Your Business",
  "recipient_number": "+1234567890",
  "message_content": "Hello from API!",
  "sim_slot": 1 // optional
}`}
              </pre>
            </div>
            
            <h3 className="mt-6">Response Format</h3>
            <pre className="bg-gray-100 p-4 rounded-lg mt-2 text-sm overflow-x-auto">
{`{
  "message_id": "uuid-here",
  "status": "queued",
  "recipient": "+1234567890"
}`}
            </pre>
          </div>
        </div>
      </div>
    </div>
  );
};

export default APIKeys;
