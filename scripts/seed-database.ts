// @ts-nocheck
import { PrismaClient } from '@prisma/client';
import { faker } from '@faker-js/faker';

const prisma = new PrismaClient();

// NJ Towns
const njTowns = [
  'Newark', 'Jersey City', 'Paterson', 'Elizabeth', 'Trenton',
  'Camden', 'Clifton', 'Passaic', 'East Orange', 'Union City',
  'Hoboken', 'Bayonne', 'Vineland', 'New Brunswick', 'Perth Amboy',
  'Atlantic City', 'Hackensack', 'Sayreville', 'North Bergen', 'Linden'
];

// Case Types for Personal Injury
const caseTypes = [
  'Motor Vehicle Accident', 'Slip and Fall', 'Medical Malpractice',
  'Product Liability', 'Workplace Injury', 'Dog Bite', 'Wrongful Death',
  'Assault/Battery', 'Premises Liability', 'Pedestrian Accident'
];

// Verbal Quality options
const verbalQualities = ['Good', 'Average', 'Poor', 'Zero', 'Excellent'];

// Task templates based on case type
const taskTemplates = {
  'Motor Vehicle Accident': [
    'Obtain police report',
    'Collect medical records',
    'Contact insurance company',
    'Schedule client interview',
    'Send demand letter',
    'Calculate damages',
    'Research similar MVA cases'
  ],
  'Slip and Fall': [
    'Obtain incident report',
    'Collect photos of scene',
    'Interview witnesses',
    'Obtain medical records',
    'Research property ownership',
    'Send demand letter'
  ],
  'Medical Malpractice': [
    'Collect all medical records',
    'Consult with medical expert',
    'Research standard of care',
    'Prepare affidavit of merit',
    'Calculate damages',
    'Review statute of limitations'
  ],
  // Default tasks for other case types
  'default': [
    'Initial client consultation',
    'Collect evidence',
    'Research applicable laws',
    'Draft demand letter',
    'Follow up with client',
    'Calculate damages estimate'
  ]
};

// Get tasks for a specific case type, with some from default list
function getTasksForCaseType(caseType, count) {
  const specificTasks = taskTemplates[caseType] || [];
  const defaultTasks = taskTemplates['default'];
  
  // Combine specific and default tasks, then select randomly
  const allPossibleTasks = [...specificTasks, ...defaultTasks];
  const selectedTasks = [];
  
  // Get random tasks up to the count
  for (let i = 0; i < count; i++) {
    const randomIndex = Math.floor(Math.random() * allPossibleTasks.length);
    const task = allPossibleTasks[randomIndex];
    
    // Avoid duplicates
    if (!selectedTasks.includes(task)) {
      selectedTasks.push(task);
    } else {
      i--; // Try again if we selected a duplicate
    }
    
    // Break if we've exhausted the task list
    if (selectedTasks.length === allPossibleTasks.length) break;
  }
  
  return selectedTasks.slice(0, count);
}

// Status options for tasks
const taskStatuses = ['Pending', 'In Progress', 'Completed', 'Overdue'];

async function seed() {
  console.log('Starting database seed...');
  
  // Create 10-15 random clients
  const clientCount = Math.floor(Math.random() * 6) + 10; // 10-15 clients
  
  const clients = [];
  
  for (let i = 0; i < clientCount; i++) {
    const firstName = faker.person.firstName();
    const lastName = faker.person.lastName();
    
    const caseType = caseTypes[Math.floor(Math.random() * caseTypes.length)];
    const verbalQuality = verbalQualities[Math.floor(Math.random() * verbalQualities.length)];
    const location = `${njTowns[Math.floor(Math.random() * njTowns.length)]}, NJ`;
    
    // Calculate random incident date (within last year)
    const incidentDate = faker.date.past({ years: 1 });
    
    // Create client
    const client = await prisma.client.create({
      data: {
        name: `${firstName} ${lastName}`,
        email: faker.internet.email({ firstName, lastName }),
        phone: faker.string.numeric('(###) ###-####'),
        incidentDate,
        location,
        injuryDetails: faker.lorem.paragraph(),
        medicalExpenses: parseFloat(faker.finance.amount({ min: 500, max: 50000, dec: 2 })),
        insuranceCompany: faker.company.name(),
        lawyerNotes: faker.lorem.paragraphs(2),
        caseType,
        verbalQuality,
      }
    });
    
    clients.push(client);
    console.log(`Created client: ${client.name}`);
    
    // Create 3-7 tasks for each client
    const taskCount = Math.floor(Math.random() * 5) + 3; // 3-7 tasks
    const taskDescriptions = getTasksForCaseType(caseType, taskCount);
    
    for (const description of taskDescriptions) {
      // Random due date between now and 3 months from now
      const dueDate = faker.date.future({ years: 0.25 });
      
      // Random status weighted towards Pending and In Progress
      const statusRandom = Math.random();
      let status;
      if (statusRandom < 0.4) status = 'Pending';
      else if (statusRandom < 0.7) status = 'In Progress';
      else if (statusRandom < 0.9) status = 'Completed';
      else status = 'Overdue';
      
      const task = await prisma.task.create({
        data: {
          clientId: client.id,
          description,
          dueDate,
          status,
          notes: Math.random() > 0.7 ? faker.lorem.paragraph() : null,
        }
      });
      
      console.log(`  Created task: ${task.description}`);
    }
    
    // Create 1-3 documents for some clients (70% chance)
    if (Math.random() < 0.7) {
      const docCount = Math.floor(Math.random() * 3) + 1; // 1-3 documents
      const docTypes = ['Representation Letter', 'Medical Release', 'Investigation Report', 'Demand Letter'];
      
      for (let j = 0; j < docCount; j++) {
        const docType = docTypes[Math.floor(Math.random() * docTypes.length)];
        
        const document = await prisma.document.create({
          data: {
            clientId: client.id,
            documentType: docType,
            fileUrl: `/documents/${client.id}/${faker.string.uuid()}.pdf`,
          }
        });
        
        console.log(`  Created document: ${document.documentType}`);
      }
    }
  }
  
  console.log(`Database seed completed. Created ${clientCount} clients with associated records.`);
}

// Run the seed function
seed()
  .catch((e) => {
    console.error('Error seeding database:', e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  }); 