// Плавная прокрутка к секциям
function scrollToSection(sectionId) {
    const section = document.getElementById(sectionId);
    if (section) {
        section.scrollIntoView({ behavior: 'smooth' });
    }
}

// Обработка отправки формы контакта
document.addEventListener('DOMContentLoaded', function() {
    const contactForm = document.querySelector('.contact-form');
    
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Получаем данные формы
            const formData = new FormData(this);
            const name = this.querySelector('input[type="text"]').value;
            const email = this.querySelector('input[type="email"]').value;
            const message = this.querySelector('textarea').value;
            
            // Показываем сообщение об успехе
            alert(`Спасибо, ${name}! Ваше сообщение отправлено. Мы свяжемся с вами на ${email}`);
            
            // Очищаем форму
            this.reset();
        });
    }

    // Обработка кнопок выбора тарифа
    const pricingButtons = document.querySelectorAll('.pricing-card .btn');
    pricingButtons.forEach(button => {
        button.addEventListener('click', function() {
            const card = this.closest('.pricing-card');
            const title = card.querySelector('h3').textContent;
            const price = card.querySelector('.amount').textContent;
            
            alert(`Вы выбрали тариф "${title}" за ${price} ₽. Перенаправление на страницу оплаты...`);
        });
    });

    // Активная ссылка в навигации
    const navLinks = document.querySelectorAll('.nav-links a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navLinks.forEach(l => l.style.color = '');
            this.style.color = 'var(--primary-color)';
        });
    });

    // Анимация при прокрутке
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -100px 0px'
    };

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    // Применяем анимацию к элементам
    const animatedElements = document.querySelectorAll('.feature-card, .pricing-card, .faq-item');
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
});

// Функция для отслеживания активной секции в навигации
window.addEventListener('scroll', function() {
    const sections = document.querySelectorAll('section');
    const navLinks = document.querySelectorAll('.nav-links a');
    
    let current = '';
    sections.forEach(section => {
        const sectionTop = section.offsetTop;
        if (pageYOffset >= sectionTop - 200) {
            current = section.getAttribute('id');
        }
    });

    navLinks.forEach(link => {
        link.style.color = '';
        if (link.getAttribute('href').slice(1) === current) {
            link.style.color = 'var(--primary-color)';
        }
    });
});
