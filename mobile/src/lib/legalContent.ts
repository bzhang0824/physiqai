// Plain-language legal content sections for PhysiqAI.
// Keeping content here lets privacy.tsx and terms.tsx stay thin.
// DRAFT — not reviewed by counsel; replace before App Store submission.

export interface LegalSection {
  heading: string;
  body: string;
}

export const PRIVACY_SECTIONS: LegalSection[] = [
  {
    heading: 'Who we are',
    body:
      'PhysiqAI is a beta product that generates a projection of your future physique using AI. ' +
      'We are currently in closed beta. Questions? Email us at brianzhangg1@gmail.com.',
  },
  {
    heading: 'What we collect',
    body:
      'We collect:\n' +
      '• Photos — a front-facing photo is required; side and back angles are optional.\n' +
      '• Body stats & goals — height, weight, body-fat estimate, training experience, and your time horizon.\n' +
      '• Email address — used only for sign-in via Supabase magic link.\n' +
      '• Weekly check-in data — optional weight, body-fat, and workout-log entries you submit after getting your projection.',
  },
  {
    heading: 'How your photos are used',
    body:
      'Your photo is used to generate a single AI image that shows a projected future physique. ' +
      'During generation, your real face pixels are composited back onto the output so your identity is preserved. ' +
      'Processing happens on-demand for your account only — we do not use your photo to train models or profile you. ' +
      'Before any photo is processed, you provide explicit consent on the consent screen.',
  },
  {
    heading: 'Where your data lives',
    body:
      'We use Supabase for authentication, database, and file storage:\n' +
      '• Raw photos are stored in a PRIVATE Supabase Storage bucket — only you and our backend can access them.\n' +
      '• Generated images and 3-D avatar frames are stored in a public bucket at long, unguessable URLs. ' +
      'Anyone with the URL can view the image, but we do not publish or index those URLs.\n' +
      'The app is hosted on Railway.',
  },
  {
    heading: 'Third-party processors',
    body:
      'We share your photo with the following sub-processors solely to operate the service:\n' +
      '• fal.ai — receives your photo over an encrypted connection to run the AI image-generation model.\n' +
      '• Supabase — database, auth, and storage.\n' +
      '• Railway — server hosting.\n' +
      'No other third parties receive your photo or personal data.',
  },
  {
    heading: 'We do not sell your data',
    body:
      'We do not sell, rent, or share your personal data or photos for advertising or any commercial purpose. ' +
      'Your content is processed only to provide the service to you.',
  },
  {
    heading: 'Retention & deletion',
    body:
      'Your photos, generated images, and check-in data are kept for as long as your account exists. ' +
      'To delete everything, go to Settings → Delete account. ' +
      'This permanently and irreversibly removes your photos, generated media, check-in history, and login. ' +
      'We complete deletion within 30 days.',
  },
  {
    heading: '18+ only',
    body:
      'PhysiqAI is intended for users who are 18 years of age or older. ' +
      'We do not knowingly collect data from anyone under 18. ' +
      'If you believe a minor has submitted data to us, contact us at brianzhangg1@gmail.com and we will delete it.',
  },
  {
    heading: 'Changes to this policy',
    body:
      'We may update this Privacy Policy as the product evolves. ' +
      'When we make material changes we will notify you by email (if you have an account) or by a notice in the app ' +
      'at least 7 days before the changes take effect.',
  },
];

export const TERMS_SECTIONS: LegalSection[] = [
  {
    heading: 'Acceptance',
    body:
      'By creating an account or using PhysiqAI you agree to these Terms of Service. ' +
      'If you do not agree, do not use the service. ' +
      'You must be 18 years of age or older to use PhysiqAI.',
  },
  {
    heading: 'Beta disclaimer',
    body:
      'PhysiqAI is currently in beta. Features may change, be removed, or behave unexpectedly. ' +
      'We may pause or discontinue the service at any time without prior notice. ' +
      'We appreciate your patience and feedback as we improve the product.',
  },
  {
    heading: 'Not medical advice',
    body:
      'PhysiqAI projections are statistical estimates based on publicly available physiology research. ' +
      'They are for motivational and informational purposes only. ' +
      'Results are not guaranteed — actual outcomes depend on genetics, adherence, health status, and many other factors. ' +
      'Nothing in this app constitutes medical, nutritional, or fitness advice. ' +
      'Consult a qualified healthcare professional before starting any new exercise or diet program.',
  },
  {
    heading: 'Acceptable use',
    body:
      'You may only upload photos of yourself, or photos of another person who has given you their explicit consent. ' +
      'You must not upload photos of minors, generate content intended to harass or deceive, ' +
      'or use the service for any unlawful purpose. ' +
      'We reserve the right to remove content and suspend accounts that violate these rules.',
  },
  {
    heading: 'Your content & our license',
    body:
      'You own the photos and content you upload. ' +
      'By using PhysiqAI you grant us a limited license to process your content solely to operate the service for you — ' +
      'generating your projection, storing results, and displaying them in the app. ' +
      'You may download and share your generated images freely. ' +
      'We will not use your images for marketing without your separate written consent.',
  },
  {
    heading: 'Account deletion',
    body:
      'You may delete your account at any time from Settings → Delete account. ' +
      'Deletion permanently removes your photos, generated media, check-in history, and login credentials.',
  },
  {
    heading: 'As-is / limitation of liability',
    body:
      'PhysiqAI is provided "as is" without warranties of any kind. ' +
      'To the maximum extent permitted by applicable law, we are not liable for indirect, incidental, ' +
      'or consequential damages arising from your use of the service. ' +
      'Our total liability to you for any claim shall not exceed the amount you paid us in the past 12 months ' +
      '(which during beta is $0).',
  },
  {
    heading: 'Termination',
    body:
      'We may suspend or terminate your access if you violate these terms or if we discontinue the service. ' +
      'You may stop using the service and delete your account at any time.',
  },
  {
    heading: 'Contact',
    body:
      'Questions about these Terms? Email us at brianzhangg1@gmail.com.',
  },
];
