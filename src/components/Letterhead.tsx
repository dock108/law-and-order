import Link from 'next/link';

export default function Letterhead() {
  return (
    <div className="w-full bg-white border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="py-6">
          <div className="flex flex-col items-center md:items-start">
            <h1 className="text-3xl md:text-4xl font-bold text-blue-900">COLACCI LAW</h1>
            <div className="mt-2 text-center md:text-left">
              <p className="text-gray-700">123 Main Street, Suite 200, Newark, NJ 07102</p>
              <p className="text-gray-700">Tel: (973) 555-1234 | Fax: (973) 555-5678</p>
              <p className="text-gray-700">Email: info@colaccilaw.com | www.colaccilaw.com</p>
            </div>
            <div className="mt-2">
              <Link 
                href="/letterhead.pdf" 
                target="_blank"
                className="text-blue-600 hover:underline text-sm"
              >
                View Official Letterhead
              </Link>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 