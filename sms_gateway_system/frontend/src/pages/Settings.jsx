import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import toast from 'react-hot-toast';
import axios from 'axios';

const Settings = () => {
  const { register, handleSubmit } = useForm();
  const [activeTab, setActiveTab] = useState('general');
  const [saving, setSaving] = useState(false);

  const onSaveGeneral = async (data) => {
    setSaving(true);
    try {
      await axios.patch('/api/v1/settings/general', data);
      toast.success('Settings saved successfully!');
    } catch (error) {
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const onSaveTelegram = async (data) => {
    setSaving(true);
    try {
      await axios.post('/api/v1/webhooks/telegram', {
        bot_token: data.bot_token,
        chat_id: data.chat_id,
        enabled: true,
        events: ['message.sent', 'message.failed', 'device.offline']
      });
      toast.success('Telegram integration configured!');
    } catch (error) {
      toast.error('Failed to configure Telegram');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-4xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">Settings</h1>
          <p className="text-gray-600 mt-1">Configure your SMS Gateway system</p>
        </div>

        {/* Tabs */}
        <div className="flex space-x-4 mb-6 border-b border-gray-200">
          <button
            onClick={() => setActiveTab('general')}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'general'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            General
          </button>
          <button
            onClick={() => setActiveTab('devices')}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'devices'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Devices
          </button>
          <button
            onClick={() => setActiveTab('telegram')}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'telegram'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Telegram Bot
          </button>
          <button
            onClick={() => setActiveTab('users')}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'users'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Users & Permissions
          </button>
          <button
            onClick={() => setActiveTab('backup')}
            className={`px-4 py-2 font-medium transition ${
              activeTab === 'backup'
                ? 'border-b-2 border-indigo-600 text-indigo-600'
                : 'text-gray-600 hover:text-gray-900'
            }`}
          >
            Backup
          </button>
        </div>

        {/* Tab Content */}
        {activeTab === 'general' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">General Settings</h2>
            <form onSubmit={handleSubmit(onSaveGeneral)} className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Send Delay Min (seconds)
                  </label>
                  <input
                    {...register('send_delay_min')}
                    type="number"
                    defaultValue={1}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Default Send Delay Max (seconds)
                  </label>
                  <input
                    {...register('send_delay_max')}
                    type="number"
                    defaultValue={3}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Sending Method
                </label>
                <select
                  {...register('sending_method')}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                >
                  <option value="sequential">Sequential (One by one)</option>
                  <option value="parallel">Parallel (Multiple at once)</option>
                  <option value="scheduled">Scheduled Batches</option>
                </select>
              </div>

              <div className="flex items-center justify-between py-4 border-t border-gray-200">
                <div>
                  <h3 className="font-medium text-gray-900">Enable Working Hours</h3>
                  <p className="text-sm text-gray-500">Only send messages during specified hours</p>
                </div>
                <input
                  {...register('working_hours_enabled')}
                  type="checkbox"
                  className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Working Hours Start
                  </label>
                  <input
                    {...register('working_hours_start')}
                    type="time"
                    defaultValue="09:00"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Working Hours End
                  </label>
                  <input
                    {...register('working_hours_end')}
                    type="time"
                    defaultValue="18:00"
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 transition"
              >
                {saving ? 'Saving...' : 'Save Settings'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'telegram' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Telegram Bot Integration</h2>
            <form onSubmit={handleSubmit(onSaveTelegram)} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Bot Token
                </label>
                <input
                  {...register('bot_token', { required: 'Bot token is required' })}
                  type="password"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Get your bot token from @BotFather on Telegram
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Chat ID
                </label>
                <input
                  {...register('chat_id', { required: 'Chat ID is required' })}
                  type="text"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  placeholder="123456789"
                />
                <p className="mt-1 text-sm text-gray-500">
                  Your Telegram user ID or group ID
                </p>
              </div>

              <div className="py-4 border-t border-gray-200">
                <h3 className="font-medium text-gray-900 mb-4">Notification Events</h3>
                <div className="space-y-3">
                  <label className="flex items-center">
                    <input {...register('notify_sent')} type="checkbox" className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">Message Sent</span>
                  </label>
                  <label className="flex items-center">
                    <input {...register('notify_failed')} type="checkbox" defaultChecked className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">Message Failed</span>
                  </label>
                  <label className="flex items-center">
                    <input {...register('notify_device_offline')} type="checkbox" defaultChecked className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">Device Offline</span>
                  </label>
                  <label className="flex items-center">
                    <input {...register('notify_daily_report')} type="checkbox" className="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                    <span className="ml-2 text-sm text-gray-700">Daily Summary Report</span>
                  </label>
                </div>
              </div>

              <button
                type="submit"
                disabled={saving}
                className="w-full py-3 px-6 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-medium rounded-lg hover:from-blue-700 hover:to-indigo-700 disabled:opacity-50 transition"
              >
                {saving ? 'Saving...' : 'Connect Telegram Bot'}
              </button>
            </form>
          </div>
        )}

        {activeTab === 'users' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Users & Permissions</h2>
            <div className="space-y-6">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-gray-900">Add New User</h3>
                  <p className="text-sm text-gray-500">Create a new user account with specific permissions</p>
                </div>
                <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
                  Add User
                </button>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="font-medium text-gray-900 mb-4">User Management Features</h3>
                <ul className="space-y-3 text-sm text-gray-600">
                  <li className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Assign specific phones to users
                  </li>
                  <li className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Set custom rate limits per user
                  </li>
                  <li className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Control send/receive permissions
                  </li>
                  <li className="flex items-center">
                    <svg className="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    Monitor user activity and usage
                  </li>
                </ul>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'backup' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Backup & Restore</h2>
            <div className="space-y-6">
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h3 className="font-medium text-green-900 mb-2">Create Backup</h3>
                <p className="text-sm text-green-700 mb-4">Download a complete backup of your messages, contacts, and settings</p>
                <button className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition">
                  Download Backup
                </button>
              </div>

              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h3 className="font-medium text-blue-900 mb-2">Restore Backup</h3>
                <p className="text-sm text-blue-700 mb-4">Restore your data from a previous backup file</p>
                <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition">
                  Upload Backup File
                </button>
              </div>

              <div className="border-t border-gray-200 pt-6">
                <h3 className="font-medium text-gray-900 mb-4">Automatic Backups</h3>
                <div className="flex items-center justify-between py-3">
                  <div>
                    <p className="font-medium text-gray-900">Enable Daily Backups</p>
                    <p className="text-sm text-gray-500">Automatically create backups every day</p>
                  </div>
                  <input type="checkbox" className="h-5 w-5 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded" />
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'devices' && (
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-6">Device Management</h2>
            <div className="space-y-4">
              <p className="text-gray-600">Manage your connected Android devices here. You can assign devices to users, configure SIM slots, and monitor device status.</p>
              <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition">
                Manage Devices
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Settings;
