import { useState } from 'react'
import './ProfileSelection.css'

const profiles = [
  { initials: 'AL', name: 'Alex L.', role: 'Bartender' },
  { initials: 'SR', name: 'Sam R.', role: 'Bartender' },
  { initials: 'JM', name: 'Jordan M.', role: 'Server' },
  { initials: 'TK', name: 'Taylor K.', role: 'Manager' },
]

export default function ProfileSelection() {
  const [selectedProfile, setSelectedProfile] = useState('Alex L.')

  return (
    <section className="profile-selection" aria-labelledby="profile-selection-title">
      <header className="profile-selection__header">
        <div className="profile-selection__brand">BARFLOW</div>
        <h1 id="profile-selection-title">
          Good evening.
          <br />
          Ready to work ?
        </h1>
        <p>
          Select your profile and log in to access the cash register.
        </p>
      </header>

      <div className="profile-selection__content">
        <div className="profile-selection__heading">
          <h2>Choose your profile</h2>
          <span>4 members of the staff</span>
        </div>

        <div className="profile-selection__grid" role="radiogroup" aria-label="Choose a profile">
          {profiles.map((profile) => (
            <button
              type="button"
              role="radio"
              aria-checked={selectedProfile === profile.name}
              className={`profile-selection__card${selectedProfile === profile.name ? ' profile-selection__card--selected' : ''}`}
              key={profile.name}
              onClick={() => setSelectedProfile(profile.name)}
            >
              <span
                className={`profile-selection__avatar${selectedProfile === profile.name ? ' profile-selection__avatar--selected' : ''}`}
              >
                {profile.initials}
              </span>
              <span className="profile-selection__info">
                <strong>{profile.name}</strong>
                <small>{profile.role}</small>
              </span>
              {selectedProfile === profile.name && (
                <span className="profile-selection__check" aria-hidden="true">✓</span>
              )}
            </button>
          ))}
        </div>

        <button className="profile-selection__help" type="button">
          <img src="/src/assets/character.svg" alt="" aria-hidden="true" />
          <span>Is this you? Find your profile</span>
          <span className="profile-selection__arrow">›</span>
        </button>
      </div>

    </section>
  )
}
