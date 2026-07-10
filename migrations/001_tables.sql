--
-- PostgreSQL database dump
--

\restrict 7YzHw79FZF2zSBvb6pi6v9PgAKmPUwGPl0NVYcZpV6tRTKOVdSUhXg3kiAJIgk0

-- Dumped from database version 18.3
-- Dumped by pg_dump version 18.3

-- Started on 2026-05-01 14:05:50

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- TOC entry 2 (class 3079 OID 16401)
-- Name: uuid-ossp; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS "uuid-ossp" WITH SCHEMA public;


--
-- TOC entry 5099 (class 0 OID 0)
-- Dependencies: 2
-- Name: EXTENSION "uuid-ossp"; Type: COMMENT; Schema: -; Owner: 
--

COMMENT ON EXTENSION "uuid-ossp" IS 'generate universally unique identifiers (UUIDs)';


SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- TOC entry 221 (class 1259 OID 16427)
-- Name: applicants; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.applicants (
    user_id uuid NOT NULL
);


ALTER TABLE public.applicants OWNER TO postgres;

--
-- TOC entry 226 (class 1259 OID 16490)
-- Name: job_skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.job_skills (
    job_id uuid NOT NULL,
    skill_id uuid NOT NULL
);


ALTER TABLE public.job_skills OWNER TO postgres;

--
-- TOC entry 223 (class 1259 OID 16449)
-- Name: jobs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.jobs (
    job_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    recruiter_id uuid NOT NULL,
    title character varying(255) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.jobs OWNER TO postgres;

--
-- TOC entry 228 (class 1259 OID 16524)
-- Name: rankings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.rankings (
    ranking_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    job_id uuid NOT NULL,
    resume_id uuid NOT NULL,
    matching_score double precision,
    candidate_rank integer
);


--
-- Name: job_applications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.job_applications (
    application_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    job_id uuid NOT NULL,
    applicant_id uuid NOT NULL,
    applied_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_job_applicant_application UNIQUE (job_id, applicant_id)
);


ALTER TABLE public.rankings OWNER TO postgres;

--
-- TOC entry 222 (class 1259 OID 16438)
-- Name: recruiters; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.recruiters (
    user_id uuid NOT NULL
);


ALTER TABLE public.recruiters OWNER TO postgres;

--
-- TOC entry 227 (class 1259 OID 16507)
-- Name: resume_skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resume_skills (
    resume_id uuid NOT NULL,
    skill_id uuid NOT NULL
);


ALTER TABLE public.resume_skills OWNER TO postgres;

--
-- TOC entry 224 (class 1259 OID 16464)
-- Name: resumes; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.resumes (
    resume_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    applicant_id uuid NOT NULL,
    raw_text text,
    file_path character varying(500),
    uploaded_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.resumes OWNER TO postgres;

--
-- TOC entry 225 (class 1259 OID 16480)
-- Name: skills; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.skills (
    skill_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    skill_name character varying(100) NOT NULL
);


ALTER TABLE public.skills OWNER TO postgres;

--
-- TOC entry 220 (class 1259 OID 16412)
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id uuid DEFAULT public.uuid_generate_v4() NOT NULL,
    email character varying(255) NOT NULL,
    password_hash character varying(255) NOT NULL,
    role character varying(20) NOT NULL,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['applicant'::character varying, 'recruiter'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- TOC entry 5086 (class 0 OID 16427)
-- Dependencies: 221
-- Data for Name: applicants; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.applicants (user_id) FROM stdin;
\.


--
-- TOC entry 5091 (class 0 OID 16490)
-- Dependencies: 226
-- Data for Name: job_skills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.job_skills (job_id, skill_id) FROM stdin;
\.


--
-- TOC entry 5088 (class 0 OID 16449)
-- Dependencies: 223
-- Data for Name: jobs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.jobs (job_id, recruiter_id, title, created_at) FROM stdin;
\.


--
-- TOC entry 5093 (class 0 OID 16524)
-- Dependencies: 228
-- Data for Name: rankings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.rankings (ranking_id, job_id, resume_id, matching_score, candidate_rank) FROM stdin;
\.


--
-- TOC entry 5087 (class 0 OID 16438)
-- Dependencies: 222
-- Data for Name: recruiters; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.recruiters (user_id) FROM stdin;
\.


--
-- TOC entry 5092 (class 0 OID 16507)
-- Dependencies: 227
-- Data for Name: resume_skills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resume_skills (resume_id, skill_id) FROM stdin;
\.


--
-- TOC entry 5089 (class 0 OID 16464)
-- Dependencies: 224
-- Data for Name: resumes; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.resumes (resume_id, applicant_id, raw_text, file_path, uploaded_at) FROM stdin;
\.


--
-- TOC entry 5090 (class 0 OID 16480)
-- Dependencies: 225
-- Data for Name: skills; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.skills (skill_id, skill_name) FROM stdin;
\.


--
-- TOC entry 5085 (class 0 OID 16412)
-- Dependencies: 220
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, email, password_hash, role) FROM stdin;
\.


--
-- TOC entry 4911 (class 2606 OID 16432)
-- Name: applicants applicants_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.applicants
    ADD CONSTRAINT applicants_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4923 (class 2606 OID 16496)
-- Name: job_skills job_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_skills
    ADD CONSTRAINT job_skills_pkey PRIMARY KEY (job_id, skill_id);


--
-- TOC entry 4915 (class 2606 OID 16458)
-- Name: jobs jobs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_pkey PRIMARY KEY (job_id);


--
-- TOC entry 4927 (class 2606 OID 16532)
-- Name: rankings rankings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rankings
    ADD CONSTRAINT rankings_pkey PRIMARY KEY (ranking_id);


--
-- TOC entry 4913 (class 2606 OID 16443)
-- Name: recruiters recruiters_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recruiters
    ADD CONSTRAINT recruiters_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4925 (class 2606 OID 16513)
-- Name: resume_skills resume_skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_skills
    ADD CONSTRAINT resume_skills_pkey PRIMARY KEY (resume_id, skill_id);


--
-- TOC entry 4917 (class 2606 OID 16474)
-- Name: resumes resumes_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_pkey PRIMARY KEY (resume_id);


--
-- TOC entry 4919 (class 2606 OID 16487)
-- Name: skills skills_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_pkey PRIMARY KEY (skill_id);


--
-- TOC entry 4921 (class 2606 OID 16489)
-- Name: skills skills_skill_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.skills
    ADD CONSTRAINT skills_skill_name_key UNIQUE (skill_name);


--
-- TOC entry 4907 (class 2606 OID 16426)
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- TOC entry 4909 (class 2606 OID 16424)
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- TOC entry 4928 (class 2606 OID 16433)
-- Name: applicants applicants_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.applicants
    ADD CONSTRAINT applicants_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- TOC entry 4932 (class 2606 OID 16497)
-- Name: job_skills job_skills_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_skills
    ADD CONSTRAINT job_skills_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- TOC entry 4933 (class 2606 OID 16502)
-- Name: job_skills job_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.job_skills
    ADD CONSTRAINT job_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(skill_id) ON DELETE CASCADE;


--
-- TOC entry 4930 (class 2606 OID 16459)
-- Name: jobs jobs_recruiter_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.jobs
    ADD CONSTRAINT jobs_recruiter_id_fkey FOREIGN KEY (recruiter_id) REFERENCES public.recruiters(user_id) ON DELETE CASCADE;


--
-- TOC entry 4936 (class 2606 OID 16533)
-- Name: rankings rankings_job_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rankings
    ADD CONSTRAINT rankings_job_id_fkey FOREIGN KEY (job_id) REFERENCES public.jobs(job_id) ON DELETE CASCADE;


--
-- TOC entry 4937 (class 2606 OID 16538)
-- Name: rankings rankings_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.rankings
    ADD CONSTRAINT rankings_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE;


--
-- TOC entry 4929 (class 2606 OID 16444)
-- Name: recruiters recruiters_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.recruiters
    ADD CONSTRAINT recruiters_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- TOC entry 4934 (class 2606 OID 16514)
-- Name: resume_skills resume_skills_resume_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_skills
    ADD CONSTRAINT resume_skills_resume_id_fkey FOREIGN KEY (resume_id) REFERENCES public.resumes(resume_id) ON DELETE CASCADE;


--
-- TOC entry 4935 (class 2606 OID 16519)
-- Name: resume_skills resume_skills_skill_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resume_skills
    ADD CONSTRAINT resume_skills_skill_id_fkey FOREIGN KEY (skill_id) REFERENCES public.skills(skill_id) ON DELETE CASCADE;


--
-- TOC entry 4931 (class 2606 OID 16475)
-- Name: resumes resumes_applicant_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.resumes
    ADD CONSTRAINT resumes_applicant_id_fkey FOREIGN KEY (applicant_id) REFERENCES public.applicants(user_id) ON DELETE CASCADE;


-- Completed on 2026-05-01 14:05:50

--
-- PostgreSQL database dump complete
--

\unrestrict 7YzHw79FZF2zSBvb6pi6v9PgAKmPUwGPl0NVYcZpV6tRTKOVdSUhXg3kiAJIgk0

