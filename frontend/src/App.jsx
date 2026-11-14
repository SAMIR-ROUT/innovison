import { useState } from 'react';
import './App.css';

function App() {
  const [sponsors, setSponsors] = useState([
    {
      id: 1,
      name: 'TechCorp',
      commitment: 500000,
      budget: 'Main Stage & Banner',
      deadline: '2026-11-20',
      status: 'Confirmed',
    },
    {
      id: 2,
      name: 'EduBrand',
      commitment: 200000,
      budget: 'Workshops & Kits',
      deadline: '2026-11-22',
      status: 'Confirmed',
    },
  ]);

  const [emailInput, setEmailInput] = useState('');
  const [aiProposal, setAiProposal] = useState(null);
  const [verifiedMsg, setVerifiedMsg] = useState('');

  const handleAnalyze = () => {
    const text = emailInput.trim();
    if (!text) {
      alert('Please paste a sponsor email message first!');
      return;
    }

    // Detect which sponsor is mentioned (defaults to TechCorp)
    const isEduBrand = text.toLowerCase().includes('edubrand');
    const targetSponsor = isEduBrand ? sponsors[1] : sponsors[0];

    // Detect numbers in the message (e.g., "3,00,000" or "300000" or "3 lakh")
    const cleaned = text.replace(/,/g, '');
    const numbers = cleaned.match(/\d+/g);
    let newAmount = 300000;

    if (numbers && numbers.length > 0) {
      const lastNum = parseInt(numbers[numbers.length - 1], 10);
      newAmount = lastNum < 100 ? lastNum * 100000 : lastNum;
    }

    const diff = targetSponsor.commitment - newAmount;

    setAiProposal({
      sponsorId: targetSponsor.id,
      sponsorName: targetSponsor.name,
      oldCommitment: targetSponsor.commitment,
      newCommitment: newAmount,
      impact:
        diff > 0
          ? `${targetSponsor.budget} budget drops by ₹${diff.toLocaleString('en-IN')}`
          : `${targetSponsor.budget} budget changes by ₹${Math.abs(diff).toLocaleString('en-IN')}`,
      suggestion: `Update ${targetSponsor.name} commitment from ₹${targetSponsor.commitment.toLocaleString('en-IN')} to ₹${newAmount.toLocaleString('en-IN')} and adjust ${targetSponsor.budget}.`,
    });
    setVerifiedMsg('');
  };

  const handleApprove = () => {
    setSponsors((prev) =>
      prev.map((item) =>
        item.id === aiProposal.sponsorId
          ? {
              ...item,
              commitment: aiProposal.newCommitment,
              status: 'Approved & Verified',
            }
          : item
      )
    );
    setVerifiedMsg(
      `Verified: ${aiProposal.sponsorName} updated from ₹${aiProposal.oldCommitment.toLocaleString('en-IN')} to ₹${aiProposal.newCommitment.toLocaleString('en-IN')}.`
    );
    setAiProposal(null);
  };

  const handleReset = () => {
    setSponsors([
      {
        id: 1,
        name: 'TechCorp',
        commitment: 500000,
        budget: 'Main Stage & Banner',
        deadline: '2026-11-20',
        status: 'Confirmed',
      },
      {
        id: 2,
        name: 'EduBrand',
        commitment: 200000,
        budget: 'Workshops & Kits',
        deadline: '2026-11-22',
        status: 'Confirmed',
      },
    ]);
    setEmailInput('');
    setAiProposal(null);
    setVerifiedMsg('');
  };

  return (
    <div style={{ maxWidth: '880px', margin: '0 auto', padding: '14px', fontFamily: 'Arial, sans-serif' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h1 style={{ margin: '0 0 8px 0', fontSize: '26px' }}>EventMind Dashboard</h1>
        <button
          type="button"
          onClick={handleReset}
          style={{ backgroundColor: '#6c757d', color: '#fff', border: 'none', padding: '8px 12px', borderRadius: '5px', cursor: 'pointer' }}
        >
          Reset Demo
        </button>
      </div>

      <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>Sponsors & Commitments</h2>
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <thead>
            <tr>
              <th style={{ textAlign: 'left', padding: '6px' }}>Sponsor</th>
              <th style={{ textAlign: 'left', padding: '6px' }}>Commitment</th>
              <th style={{ textAlign: 'left', padding: '6px' }}>Budget</th>
              <th style={{ textAlign: 'left', padding: '6px' }}>Deadline</th>
              <th style={{ textAlign: 'left', padding: '6px' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {sponsors.map((s) => (
              <tr key={s.id}>
                <td style={{ padding: '6px' }}>{s.name}</td>
                <td style={{ padding: '6px' }}>₹{s.commitment.toLocaleString('en-IN')}</td>
                <td style={{ padding: '6px' }}>{s.budget}</td>
                <td style={{ padding: '6px' }}>{s.deadline}</td>
                <td style={{ padding: '6px' }}>{s.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '18px' }}>Smart Input (Paste Sponsor Email Message)</h2>
        <textarea
          rows="2"
          style={{ width: '100%', padding: '8px', marginBottom: '8px', boxSizing: 'border-box' }}
          placeholder="Example: Hi team, TechCorp can only sponsor 3,00,000 now."
          value={emailInput}
          onChange={(e) => setEmailInput(e.target.value)}
        />
        <button
          type="button"
          onClick={handleAnalyze}
          style={{ backgroundColor: '#007bff', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '5px', cursor: 'pointer' }}
        >
          Analyze with AI
        </button>
      </div>

      {aiProposal && (
        <div style={{ border: '1px solid #e0a800', backgroundColor: '#fff3cd', color: '#111', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
          <h3 style={{ margin: '0 0 6px 0' }}>AI Recommendation</h3>
          <p style={{ margin: '4px 0' }}>
            <strong>Change:</strong> ₹{aiProposal.oldCommitment.toLocaleString('en-IN')} → ₹{aiProposal.newCommitment.toLocaleString('en-IN')}
          </p>
          <p style={{ margin: '4px 0' }}><strong>Impact:</strong> {aiProposal.impact}</p>
          <p style={{ margin: '4px 0 10px 0' }}><strong>Suggestion:</strong> {aiProposal.suggestion}</p>
          <button
            type="button"
            onClick={handleApprove}
            style={{ backgroundColor: '#28a745', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '5px', cursor: 'pointer', marginRight: '10px' }}
          >
            Approve Update
          </button>
          <button
            type="button"
            onClick={() => setAiProposal(null)}
            style={{ backgroundColor: '#dc3545', color: '#fff', border: 'none', padding: '8px 14px', borderRadius: '5px', cursor: 'pointer' }}
          >
            Dismiss
          </button>
        </div>
      )}

      {verifiedMsg && (
        <div style={{ border: '1px solid #28a745', backgroundColor: '#d4edda', color: '#155724', borderRadius: '8px', padding: '12px' }}>
          {verifiedMsg}
        </div>
      )}
    </div>
  );
}

export default App;